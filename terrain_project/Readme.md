Terrain 3D Project
这是一个基于 Vue.js 开发的地理数据可视化项目，旨在通过整合 JAXA AW3D30 数字表面模型 (DSM) 与 Natural Earth 矢量边界，实现高精度的 3D 地形渲染与地理交互。

功能特性
3D 地形渲染: 使用 [Three.js/Cesium/Plotly] 将 16-bit 原始高程数据转换为动态 3D 网格。
地理要素叠加: 在地形模型上精准叠加国家边界、河流及主要城市坐标。
多源数据融合: 整合了卫星栅格数据 (TIFF) 与矢量地理信息 (Shapefile)。
数据预处理: 内置 Python 脚本，支持将高程数据归一化并转换为前端友好的 GeoJSON/PNG 格式。

问题：
Three.js正在尝试修改，因为瓦片集中于一个文件当中，运行内存太大，python读取.tif以及.shp可以下采样，因此先用python做个demo.
