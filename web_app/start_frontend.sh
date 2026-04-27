#!/bin/bash

# 启动前端服务
echo "Starting frontend server..."
python3 -m http.server 8001 --directory frontend
