from fastapi_socketio import SocketManager
from fastapi import FastAPI
import socketio
from typing import Dict, Set
import json
import asyncio
from datetime import datetime
from .config import settings

class WebSocketManager:
    def __init__(self):
        self.sio = None  # SocketManager 返回的 server
        self.connected_users: Dict[str, dict] = {}
        self.user_rooms: Dict[str, Set[str]] = {}

    def mount_to_app(self, app: FastAPI):
        """挂载到FastAPI应用"""
        # 使用 fastapi_socketio 的 SocketManager
        # 它会创建自己的 socketio server 并挂载到 /socket.io 路径
        self.sio = SocketManager(app=app, cors_allowed_origins=settings.ALLOWED_ORIGINS)
        self._register_events()

    def _register_events(self):
        """注册Socket.IO事件"""

        @self.sio.on('connect')
        async def connect(sid, environ):
            """客户端连接事件"""
            print(f"Client connected: {sid}")

            # 发送连接确认
            await self.sio.emit('connected', {
                'message': 'Connected successfully',
                'sid': sid,
                'timestamp': datetime.now().isoformat()
            }, to=sid)
            print(f"Client {sid} connected")

        @self.sio.on('disconnect')
        async def disconnect(sid):
            """客户端断开连接事件"""
            print(f"Client disconnected: {sid}")

            # 清理用户信息
            if sid in self.connected_users:
                user_info = self.connected_users[sid]
                print(f"User {user_info.get('username')} disconnected")
                del self.connected_users[sid]

        @self.sio.on('join_task_monitor')
        async def join_task_monitor(sid, data):
            """加入任务监控房间"""
            task_id = data.get('task_id')
            if task_id:
                room_name = f"task_{task_id}"
                await self.sio.enter_room(sid, room_name)

                # 发送确认消息
                await self.sio.emit('joined_task_monitor', {
                    'task_id': task_id,
                    'message': f'Joined monitoring for task {task_id}'
                }, to=sid)

                print(f"Client {sid} joined task monitoring room: {room_name}")

        @self.sio.on('leave_task_monitor')
        async def leave_task_monitor(sid, data):
            """离开任务监控房间"""
            task_id = data.get('task_id')
            if task_id:
                room_name = f"task_{task_id}"
                await self.sio.leave_room(sid, room_name)

                await self.sio.emit('left_task_monitor', {
                    'task_id': task_id,
                    'message': f'Left monitoring for task {task_id}'
                }, to=sid)

        @self.sio.on('broadcast_task_update')
        async def broadcast_task_update(sid, data):
            """广播任务更新"""
            task_id = data.get('task_id')
            if task_id:
                room_name = f"task_{task_id}"

                # 添加时间戳
                data['timestamp'] = datetime.now().isoformat()
                data['from_sid'] = sid

                # 向房间内的所有客户端广播
                await self.sio.emit('task_update', data, room=room_name, skip_sid=sid)

        @self.sio.on('performance_data')
        async def performance_data(sid, data):
            """处理性能数据"""
            task_id = data.get('task_id')
            if task_id:
                room_name = f"task_{task_id}"

                # 添加元数据
                data['timestamp'] = datetime.now().isoformat()
                data['type'] = 'performance'

                # 广播性能数据
                await self.sio.emit('performance_update', data, room=room_name)

        @self.sio.on('system_status')
        async def system_status(sid, data):
            """系统状态更新"""
            # 广播给所有连接的客户端
            data['timestamp'] = datetime.now().isoformat()
            await self.sio.emit('system_status_update', data)

        @self.sio.on('ping')
        async def ping(sid, data):
            """客户端心跳请求"""
            await self.sio.emit('pong', {'timestamp': datetime.now().isoformat()}, to=sid)

        @self.sio.on('join_node_partition_monitor')
        async def join_node_partition_monitor(sid, data):
            """加入节点分区监控房间"""
            monitor_id = data.get('monitor_id')
            if monitor_id:
                room_name = f"node_partition_{monitor_id}"
                await self.sio.enter_room(sid, room_name)

                await self.sio.emit('joined_node_partition_monitor', {
                    'monitor_id': monitor_id,
                    'message': f'Joined node partition monitoring {monitor_id}'
                }, to=sid)

                print(f"Client {sid} joined node partition monitoring room: {room_name}")

        @self.sio.on('leave_node_partition_monitor')
        async def leave_node_partition_monitor(sid, data):
            """离开节点分区监控房间"""
            monitor_id = data.get('monitor_id')
            if monitor_id:
                room_name = f"node_partition_{monitor_id}"
                await self.sio.leave_room(sid, room_name)

                await self.sio.emit('left_node_partition_monitor', {
                    'monitor_id': monitor_id,
                    'message': f'Left node partition monitoring {monitor_id}'
                }, to=sid)

    async def broadcast_to_task(self, task_id: str, event: str, data: dict):
        """向特定任务房间广播消息"""
        room_name = f"task_{task_id}"
        data['timestamp'] = datetime.now().isoformat()
        await self.sio.emit(event, data, room=room_name)

    async def broadcast_to_user(self, user_id: str, event: str, data: dict):
        """向特定用户房间广播消息"""
        room_name = f"user_{user_id}"
        data['timestamp'] = datetime.now().isoformat()
        await self.sio.emit(event, data, room=room_name)

    async def broadcast_global(self, event: str, data: dict):
        """全局广播消息"""
        data['timestamp'] = datetime.now().isoformat()
        await self.sio.emit(event, data)

    async def broadcast_to_node_partition(self, monitor_id: str, event: str, data: dict):
        """向节点分区监控房间广播消息"""
        room_name = f"node_partition_{monitor_id}"
        data['timestamp'] = datetime.now().isoformat()
        await self.sio.emit(event, data, room=room_name)

    def get_connected_clients(self) -> Dict[str, dict]:
        """获取所有连接的客户端信息"""
        return self.connected_users.copy()

    def get_client_count(self) -> int:
        """获取连接客户端数量"""
        return len(self.connected_users)


# 创建全局WebSocket管理器实例
socket_manager = WebSocketManager()
