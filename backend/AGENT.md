# 项目须知

## 项目预览

- 本项目是为前端（D3.js）可视化项目提供数据的后端服务，主要目标参见计划文档[planA.md]

- 本项目使用`uv包管理器`管理python虚拟环境，若要运行test.py，请运行`uv run test.py`

## 项目结构

- `doc/`：项目文档，包括接口文档[doc/interface.md]、数据字典[doc/data-schema.md]和数据溯源文档[doc/data-provenance.md]
- `data/`：原数据，通过脚本下载或手动处理生成
- `src/`：使用`fastapi`作为框架的后端服务源代码
- `scripts/`：用于批量下载或生成数据的脚本
- `tests/`：测试脚本，用于对后端提供的API做正确性和性能测试

## 项目规范

- 接口设计应该遵从**单一职责**，**响应统一**，**遵循RESTFUL规范**的原则
- 接口实现之后应该先检查有无明显的语法错误，再编写测试文件，使用`uv run pytest -q tests/test_new_interface.py`运行单元测试，再使用`uv run pytest -q tests/`运行集成测试，确认测试全部通过后，更新接口文档[doc/interface.md]（由于数据过大，可能测试时需要使用轻量模式以避免缓冲区异常：设置环境变量`LIGHTMODE=1`）
