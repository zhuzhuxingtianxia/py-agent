# -*- coding: utf-8 -*-
"""
@Project: Python01
@File: websocket_client.py
@Time: 2025/7/24
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
import asyncio
import websockets
import json
import random
import argparse
from datetime import datetime


class WebSocketClient:
    def __init__(self, username, password, server_url="ws://localhost:8765"):
        self.username = username
        self.password = password
        self.server_url = server_url
        self.websocket = None
        self.current_room = None
        self.user_info = None
        print(f"客户端初始化: {username} 连接到 {server_url}")

    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            print("连接服务器成功")

            # 发送认证信息
            await self.websocket.send(json.dumps({
                "username": self.username,
                "password": self.password
            }))

            # 等待认证响应
            response = await self.websocket.recv()
            response_data = json.loads(response)

            if response_data.get("type") == "auth_success":
                self.user_info = response_data.get("user")
                print(f"认证成功! 欢迎 {self.user_info['username']} (角色: {self.user_info['role']})")

                # 接收房间列表
                room_list = await self.websocket.recv()
                room_data = json.loads(room_list)
                if room_data.get("type") == "room_list":
                    print(f"可用房间: {', '.join(room_data['rooms'])}")

            else:
                print(f"认证失败: {response_data.get('message', '未知错误')}")
                await self.close()
                return False

            return True

        except Exception as e:
            print(f"连接失败: {str(e)}")
            return False

    async def join_room(self, room_name):
        """加入聊天室"""
        if self.websocket:
            await self.websocket.send(json.dumps({
                "type": "join_room",
                "room": room_name
            }))
            self.current_room = room_name
            print(f"已加入房间: {room_name}")

    async def leave_room(self):
        """离开当前房间"""
        if self.websocket and self.current_room:
            await self.websocket.send(json.dumps({
                "type": "leave_room",
                "room": self.current_room
            }))
            print(f"已离开房间: {self.current_room}")
            self.current_room = None

    async def send_message(self, content):
        """发送消息到当前房间"""
        if self.websocket and self.current_room:
            await self.websocket.send(json.dumps({
                "type": "chat_message",
                "room": self.current_room,
                "content": content
            }))
            print(f"消息已发送: {content}")

    async def send_direct_message(self, target, content):
        """发送私信"""
        if self.websocket:
            await self.websocket.send(json.dumps({
                "type": "direct_message",
                "target": target,
                "content": content
            }))
            print(f"私信已发送给 {target}: {content}")

    async def listen(self):
        """监听服务器消息"""
        try:
            async for message in self.websocket:
                await self.handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            print("连接已关闭")

    async def handle_message(self, message):
        """处理服务器消息"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "chat_message":
                msg = data.get("message", {})
                print(f"[{msg.get('room')}] {msg.get('user')} ({msg.get('timestamp')}): {msg.get('content')}")

            elif msg_type == "direct_message":
                print(f"[私信] {data.get('from')} -> 你: {data.get('content')}")

            elif msg_type == "user_joined":
                print(f"[系统] {data.get('user')} 加入了房间 {data.get('room')}")

            elif msg_type == "user_left":
                print(f"[系统] {data.get('user')} 离开了房间 {data.get('room')}")

            elif msg_type == "server_status":
                status = data
                print(f"[服务器状态] 客户端数: {status.get('clients')}, 房间状态: {status.get('rooms')}")

            elif msg_type == "room_joined":
                print(f"成功加入房间 {data.get('room')}")
                history = data.get("history", [])
                if history:
                    print("--- 历史消息 ---")
                    for msg in history:
                        print(f"[历史] {msg.get('user')}: {msg.get('content')}")
                    print("---------------")

            else:
                print(f"未知消息类型: {msg_type}")

        except json.JSONDecodeError:
            print(f"收到非JSON消息: {message}")

    async def close(self):
        """关闭连接"""
        if self.websocket:
            if self.current_room:
                await self.leave_room()
            await self.websocket.close()
            print("连接已关闭")

    async def run(self, room="general"):
        """运行客户端"""
        connected = await self.connect()
        if not connected:
            return

        await self.join_room(room)

        # 启动监听任务
        listen_task = asyncio.create_task(self.listen())

        # 模拟用户交互
        try:
            while True:
                message = input("输入消息 (或输入 '/exit' 退出): ")
                if message == '/exit':
                    break
                elif message.startswith('/join '):
                    new_room = message.split(' ', 1)[1]
                    await self.leave_room()
                    await self.join_room(new_room)
                elif message.startswith('/pm '):
                    parts = message.split(' ', 2)
                    if len(parts) == 3:
                        target = parts[1]
                        content = parts[2]
                        await self.send_direct_message(target, content)
                    else:
                        print("私信格式: /pm [用户名] [消息]")
                else:
                    await self.send_message(message)
        finally:
            listen_task.cancel()
            await self.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='WebSocket 客户端')
    parser.add_argument('--username', type=str, default="alice", help='用户名')
    parser.add_argument('--password', type=str, default="pass123", help='密码')
    parser.add_argument('--room', type=str, default="general", help='加入的房间')
    parser.add_argument('--server', type=str, default="ws://localhost:8765", help='服务器地址')

    args = parser.parse_args()

    client = WebSocketClient(
        username=args.username,
        password=args.password,
        server_url=args.server
    )

    asyncio.run(client.run(room=args.room))