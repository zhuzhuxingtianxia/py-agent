# -*- coding: utf-8 -*-
"""
@Project: Python01
@File: WebSocketServer.py
@Time: 2025/7/24
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
import asyncio
import websockets
import json
import random
import logging
from datetime import datetime
from uuid import uuid4

from websockets import ServerConnection

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("websocket_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WebSocketServer")

# 存储所有连接的客户端
connected_clients = set()

# 用户数据库模拟
users_db = {
    "alice": {"password": "pass123", "role": "admin"},
    "bob": {"password": "bobpass", "role": "user"},
    "charlie": {"password": "charliepass", "role": "user"}
}

# 房间管理
chat_rooms = {
    "general": set(),
    "tech": set(),
    "random": set()
}

# 消息历史记录
message_history = {
    "general": [],
    "tech": [],
    "random": []
}


class WebSocketServer:
    def __init__(self, host='0.0.0.0', port=8765):
        self.host = host
        self.port = port
        self.server = None
        logger.info(f"WebSocket 服务器初始化: {host}:{port}")

    async def authenticate(self, websocket, credentials):
        """用户认证"""
        try:
            data = json.loads(credentials)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return False, "缺少用户名或密码"

            user = users_db.get(username)
            if not user:
                return False, "用户不存在"

            if user['password'] != password:
                return False, "密码错误"

            return True, {"username": username, "role": user['role']}
        except Exception as e:
            logger.error(f"认证错误: {str(e)}")
            return False, "认证失败"

    async def handle_client(self, websocket: ServerConnection):
        """处理客户端连接"""
        client_id = str(uuid4())[:8]
        logger.info(f"新客户端连接: {client_id}")
        connected_clients.add(websocket)

        try:
            # 等待认证消息
            credentials = await websocket.recv()
            auth_success, auth_response = await self.authenticate(websocket, credentials)

            if not auth_success:
                await websocket.send(json.dumps({
                    "type": "auth_error",
                    "message": auth_response
                }))
                return

            user_info = auth_response
            logger.info(f"用户认证成功: {user_info['username']}")
            await websocket.send(json.dumps({
                "type": "auth_success",
                "user": user_info
            }))

            # 发送房间列表
            await websocket.send(json.dumps({
                "type": "room_list",
                "rooms": list(chat_rooms.keys())
            }))

            # 主消息循环
            async for message in websocket:
                await self.process_message(websocket, message, user_info)

        except websockets.exceptions.ConnectionClosedOK:
            logger.info(f"客户端 {client_id} 正常断开连接")
        except websockets.exceptions.ConnectionClosedError:
            logger.error(f"客户端 {client_id} 异常断开连接")
        except Exception as e:
            logger.error(f"处理客户端 {client_id} 时发生错误: {str(e)}")
        finally:
            # 清理客户端
            connected_clients.discard(websocket)
            # 从所有房间移除
            for room in chat_rooms.values():
                room.discard(websocket)
            logger.info(f"客户端 {client_id} 已清理")

    async def process_message(self, websocket, message, user_info):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == "join_room":
                room = data.get('room')
                if room in chat_rooms:
                    chat_rooms[room].add(websocket)
                    await websocket.send(json.dumps({
                        "type": "room_joined",
                        "room": room,
                        "history": message_history[room][-20:]  # 发送最近20条消息
                    }))
                    await self.broadcast({
                        "type": "user_joined",
                        "room": room,
                        "user": user_info['username']
                    }, room, exclude=[websocket])

            elif msg_type == "leave_room":
                room = data.get('room')
                if room in chat_rooms and websocket in chat_rooms[room]:
                    chat_rooms[room].discard(websocket)
                    await self.broadcast({
                        "type": "user_left",
                        "room": room,
                        "user": user_info['username']
                    }, room, exclude=[websocket])

            elif msg_type == "chat_message":
                room = data.get('room')
                content = data.get('content')
                if room in chat_rooms and websocket in chat_rooms[room]:
                    # 创建消息对象
                    msg_obj = {
                        "id": str(uuid4()),
                        "timestamp": datetime.now().isoformat(),
                        "user": user_info['username'],
                        "content": content,
                        "room": room
                    }
                    # 保存到历史记录
                    message_history[room].append(msg_obj)
                    # 广播消息
                    await self.broadcast({
                        "type": "chat_message",
                        "message": msg_obj
                    }, room)

            elif msg_type == "direct_message":
                target_user = data.get('target')
                content = data.get('content')
                # 在实际应用中，这里需要查找目标用户的连接
                # 这里简化为广播给所有用户
                await self.broadcast({
                    "type": "direct_message",
                    "from": user_info['username'],
                    "to": target_user,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }, room=None)

            else:
                logger.warning(f"未知消息类型: {msg_type}")

        except json.JSONDecodeError:
            logger.error("消息格式错误: 非JSON格式")
        except Exception as e:
            logger.error(f"处理消息时出错: {str(e)}")

    async def broadcast(self, message, room=None, exclude=None):
        """广播消息"""
        if exclude is None:
            exclude = []

        message_json = json.dumps(message)

        if room:
            # 广播到指定房间
            recipients = chat_rooms[room] - set(exclude)
        else:
            # 广播到所有连接
            recipients = connected_clients - set(exclude)

        if recipients:
            await asyncio.gather(*[
                client.send(message_json)
                for client in recipients
            ])

    async def status_updates(self):
        """定时发送服务器状态更新"""
        while True:
            await asyncio.sleep(10)
            status = {
                "type": "server_status",
                "timestamp": datetime.now().isoformat(),
                "clients": len(connected_clients),
                "rooms": {room: len(clients) for room, clients in chat_rooms.items()}
            }
            await self.broadcast(status)

    async def start(self):
        """启动服务器"""
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        logger.info(f"WebSocket 服务器启动在 ws://{self.host}:{self.port}")

        # 启动状态更新任务
        asyncio.create_task(self.status_updates())

        # 保持服务器运行
        await self.server.wait_closed()

    def run(self):
        """运行服务器"""
        asyncio.run(self.start())


if __name__ == "__main__":
    server = WebSocketServer()
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("服务器关闭")