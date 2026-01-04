#!/bin/bash
# PyPI 发布辅助脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== NetPulse SDK 发布脚本 ===${NC}\n"

# 检查是否在正确的目录
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED} 错误：请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 检查 PyPI 凭证配置
PYPI_RC="$HOME/.pypirc"
if [ ! -f "$PYPI_RC" ]; then
    echo -e "${YELLOW}  未找到 PyPI 凭证配置文件: $PYPI_RC${NC}"
    echo ""
    echo "请创建配置文件并添加你的 API Token："
    echo ""
    echo -e "${YELLOW}创建文件: $PYPI_RC${NC}"
    echo ""
    echo "文件内容示例："
    echo -e "${GREEN}[distutils]${NC}"
    echo -e "${GREEN}index-servers =${NC}"
    echo -e "${GREEN}    pypi${NC}"
    echo -e "${GREEN}    testpypi${NC}"
    echo ""
    echo -e "${GREEN}[pypi]${NC}"
    echo -e "${GREEN}username = __token__${NC}"
    echo -e "${GREEN}password = pypi-YOUR-API-TOKEN${NC}"
    echo ""
    echo -e "${GREEN}[testpypi]${NC}"
    echo -e "${GREEN}repository = https://test.pypi.org/legacy/${NC}"
    echo -e "${GREEN}username = __token__${NC}"
    echo -e "${GREEN}password = pypi-YOUR-TEST-API-TOKEN${NC}"
    echo ""
    echo "获取 API Token："
    echo "  - PyPI: https://pypi.org/manage/account/token/"
    echo "  - TestPyPI: https://test.pypi.org/manage/account/token/"
    echo ""
    read -p "是否现在创建配置文件? [y/N]: " CREATE_CONFIG
    if [ "$CREATE_CONFIG" = "y" ] || [ "$CREATE_CONFIG" = "Y" ]; then
        read -p "输入 PyPI API Token (pypi-开头): " PYPI_TOKEN
        read -p "输入 TestPyPI API Token (pypi-开头，可选，直接回车跳过): " TESTPYPI_TOKEN
        
        cat > "$PYPI_RC" << EOF
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = ${PYPI_TOKEN}

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = ${TESTPYPI_TOKEN:-${PYPI_TOKEN}}
EOF
        chmod 600 "$PYPI_RC"
        echo -e "${GREEN} 配置文件已创建: $PYPI_RC${NC}"
        echo ""
    else
        echo -e "${RED} 需要配置 PyPI 凭证才能继续${NC}"
        exit 1
    fi
else
    echo -e "${GREEN} 找到 PyPI 凭证配置: $PYPI_RC${NC}"
    # 检查是否包含 token
    if ! grep -q "password = pypi-" "$PYPI_RC" 2>/dev/null; then
        echo -e "${YELLOW}  警告：配置文件中可能没有有效的 API Token${NC}"
        echo "请确保 password 字段包含以 'pypi-' 开头的 API Token"
        echo ""
    fi
fi
echo ""

# 读取当前版本
CURRENT_VERSION=$(grep "version = " pyproject.toml | head -1 | sed 's/.*"\(.*\)".*/\1/')
echo -e "${YELLOW}当前版本: ${CURRENT_VERSION}${NC}"
echo ""

# 询问发布类型
echo "选择发布类型:"
echo "1) TestPyPI (测试)"
echo "2) PyPI (正式)"
read -p "请选择 [1/2]: " PUBLISH_TYPE

if [ "$PUBLISH_TYPE" != "1" ] && [ "$PUBLISH_TYPE" != "2" ]; then
    echo -e "${RED} 无效选择${NC}"
    exit 1
fi

# 询问是否更新版本号
read -p "是否需要更新版本号? [y/N]: " UPDATE_VERSION
if [ "$UPDATE_VERSION" = "y" ] || [ "$UPDATE_VERSION" = "Y" ]; then
    read -p "输入新版本号 (当前: ${CURRENT_VERSION}): " NEW_VERSION
    if [ -n "$NEW_VERSION" ]; then
        # 更新 pyproject.toml
        sed -i "s/version = \"${CURRENT_VERSION}\"/version = \"${NEW_VERSION}\"/" pyproject.toml
        # 更新 __init__.py
        sed -i "s/__version__ = \"${CURRENT_VERSION}\"/__version__ = \"${NEW_VERSION}\"/" netpulse_sdk/__init__.py
        echo -e "${GREEN} 版本号已更新: ${CURRENT_VERSION} → ${NEW_VERSION}${NC}"
        CURRENT_VERSION=$NEW_VERSION
    fi
fi

echo ""
echo -e "${YELLOW}=== 步骤 1: 代码检查 ===${NC}"
echo "运行 ruff 检查..."
if ! ruff check netpulse_sdk/; then
    echo -e "${RED} 代码检查失败${NC}"
    exit 1
fi

if ! ruff format --check netpulse_sdk/; then
    echo -e "${YELLOW}  代码格式不规范，正在格式化...${NC}"
    ruff format netpulse_sdk/
fi
echo -e "${GREEN} 代码检查通过${NC}\n"

echo -e "${YELLOW}=== 步骤 2: 清理旧构建 ===${NC}"
rm -rf dist/ build/ *.egg-info netpulse_sdk.egg-info
echo -e "${GREEN} 清理完成${NC}\n"

echo -e "${YELLOW}=== 步骤 3: 构建包 ===${NC}"
python3 -m build
if [ $? -ne 0 ]; then
    echo -e "${RED} 构建失败${NC}"
    exit 1
fi
echo -e "${GREEN} 构建完成${NC}\n"

echo -e "${YELLOW}=== 步骤 4: 检查包完整性 ===${NC}"
twine check dist/*
if [ $? -ne 0 ]; then
    echo -e "${RED} 包检查失败${NC}"
    exit 1
fi
echo -e "${GREEN} 包检查通过${NC}\n"

echo -e "${YELLOW}=== 步骤 5: 上传包 ===${NC}"
if [ "$PUBLISH_TYPE" = "1" ]; then
    echo "上传到 TestPyPI..."
    twine upload --repository testpypi dist/*
    echo ""
    echo -e "${GREEN} 已上传到 TestPyPI${NC}"
    echo ""
    echo "测试安装命令:"
    echo -e "${YELLOW}pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ netpulse-sdk==${CURRENT_VERSION}${NC}"
else
    read -p "确认上传到正式 PyPI? [y/N]: " CONFIRM
    if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        echo -e "${YELLOW}已取消发布${NC}"
        exit 0
    fi
    echo "上传到 PyPI..."
    twine upload dist/*
    echo ""
    echo -e "${GREEN} 已上传到 PyPI${NC}"
    echo ""
    echo "安装命令:"
    echo -e "${YELLOW}pip install netpulse-sdk==${CURRENT_VERSION}${NC}"
    echo ""
    echo "建议创建 Git Tag:"
    echo -e "${YELLOW}git tag v${CURRENT_VERSION}${NC}"
    echo -e "${YELLOW}git push origin v${CURRENT_VERSION}${NC}"
fi

echo ""
echo -e "${GREEN} 发布完成！${NC}"

