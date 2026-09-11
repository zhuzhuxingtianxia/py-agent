# -*- coding: utf-8 -*-
"""
@Project: Python01
@File: SocketServer.py
@Time: 2025/7/23
@Author: hil
@Desc:
~~~~~~~~~~~~~~~~~~~~~~~~
"""
import asyncio
import json
import websockets
from websockets import ServerConnection


# WebSocket 处理函数
async def echo(websocket: ServerConnection):
    print(f"客户端已连接")
    try:
        # await websocket.send(json.dumps({"type": "ping"}))
        async for message in websocket:
            print(f"收到消息: {json.loads(message)}")
            # 将消息返回给客户端
            await websocket.send(message)
    except websockets.exceptions.ConnectionClosed:
        print("客户端已断开连接")

# WebSocket 服务器主函数
async def main():
    host = "172.17.131.46"
    async with websockets.serve(
            echo,
            host,
            8765,
        ) as server:
        print(f"WebSocket 服务器正在运行，地址: ws://{host}:8765")
        await server.serve_forever() # 永远运行

if __name__ == "__main__":
    # 启动事件循环并运行异步主函数 ✅
    asyncio.run(main())
