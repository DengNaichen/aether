import subprocess
import time
import uuid
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
import os
import re
import pytest
from typing import Iterator

# --- Configuration Constants ---
# 将所有配置集中到这里，方便管理
NEO4J_IMAGE = "neo4j:5.18.1"
NEO4J_CONTAINER_NAME = "test-neo4j"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "testpassword"
HEALTH_CHECK_TIMEOUT = 60  # seconds


@pytest.fixture(scope="session", autouse=True)
def clean_environment_before_session():
    """
    (关键修复) 这个 autouse fixture 会在整个测试会话开始前自动运行，
    确保删掉可能由上一次失败的测试留下的环境变量，
    防止应用在导入时就创建了被污染的数据库驱动实例。
    """
    problematic_var = "NEO4J_URI"
    if problematic_var in os.environ:
        del os.environ[problematic_var]
    yield


@pytest.fixture(scope="session")
def neo4j_docker() -> Iterator[str]:
    """
    启动一个用于测试的 Neo4j Docker 容器。
    这个 fixture 会等待数据库完全准备好接受连接，而不是使用固定的 sleep 时间。
    它会在测试会话结束后自动清理并移除容器。
    """
    # 启动前先清理可能存在的旧容器
    subprocess.run(["docker", "rm", "-f", NEO4J_CONTAINER_NAME],
                   capture_output=True)

    # 定义 Docker run 命令
    docker_command = [
        "docker", "run", "-d",
        "--name", NEO4J_CONTAINER_NAME,
        "-p", "0:7687",
        "-e", f"NEO4J_AUTH={NEO4J_USER}/{NEO4J_PASSWORD}",
        NEO4J_IMAGE
    ]

    run_result = subprocess.run(docker_command, capture_output=True, text=True)
    if run_result.returncode != 0:
        raise RuntimeError(f"Docker Run Failed: {run_result.stderr}")

    # 获取动态映射的主机端口
    port_info = subprocess.check_output(
        ["docker", "port", NEO4J_CONTAINER_NAME, "7687"], text=True
    ).strip()
    host_port = re.search(r":(\d+)$", port_info).group(1)
    neo4j_uri = f"bolt://localhost:{host_port}"

    # --- 健康检查 ---
    start_time = time.time()
    while time.time() - start_time < HEALTH_CHECK_TIMEOUT:
        try:
            driver = GraphDatabase.driver(neo4j_uri,
                                          auth=(NEO4J_USER, NEO4J_PASSWORD))
            with driver:
                driver.verify_connectivity()
            print(f"\n✅ Neo4j container is ready at {neo4j_uri}")
            break
        except ServiceUnavailable:
            time.sleep(1)
    else:
        raise RuntimeError("Neo4j container failed to start in time.")

    # 设置环境变量，供应用代码在测试时使用
    os.environ["NEO4J_URI"] = neo4j_uri
    os.environ["NEO4J_USER"] = NEO4J_USER
    os.environ["NEO4J_PASSWORD"] = NEO4J_PASSWORD

    yield neo4j_uri

    # --- Teardown: 清理容器 ---
    print(f"\n🗑️ Tearing down Neo4j container '{NEO4J_CONTAINER_NAME}'...")
    subprocess.run(["docker", "rm", "-f", NEO4J_CONTAINER_NAME],
                   capture_output=True)


@pytest.fixture(scope="session")
def test_neo4j_db(neo4j_docker: str) -> Iterator[str]:
    """
    在测试容器中创建一个隔离的数据库实例，并在测试结束后清理。
    """
    # ✨ 核心修复：直接使用由 neo4j_docker 传入的干净的 base_uri，
    # 避免从可能被污染的环境变量中读取。
    base_uri = neo4j_docker
    user = os.environ["NEO4J_USER"]
    password = os.environ["NEO4J_PASSWORD"]
    db_name = f'test_db_{uuid.uuid4().hex[:8]}'

    # 使用临时 driver 进行数据库的创建和状态检查
    with GraphDatabase.driver(base_uri, auth=(user, password)) as setup_driver:
        setup_driver.execute_query(f"CREATE DATABASE {db_name} IF NOT EXISTS", database_="system")
        while True:
            result = setup_driver.execute_query("SHOW DATABASE $db_name", db_name=db_name, database_="system")
            record = result.records[0] if result.records else None
            if record and record['currentStatus'] == 'online':
                break
            time.sleep(0.5)

    # 修改环境变量，让应用在测试期间连接到这个新创建的数据库
    original_uri = os.environ.get("NEO4J_URI", "")
    os.environ["NEO4J_URI"] = f"{base_uri}?database={db_name}"

    yield db_name

    # --- Teardown: 清理数据库 ---
    if original_uri:
        os.environ["NEO4J_URI"] = original_uri
    else:
        if "NEO4J_URI" in os.environ:
             del os.environ["NEO4J_URI"]

    try:
        # 清理时也必须使用干净的 base_uri
        with GraphDatabase.driver(base_uri, auth=(user, password)) as cleanup_driver:
            cleanup_driver.execute_query(f"DROP DATABASE {db_name} IF EXISTS", database_="system")
        print(f"\n✅ Successfully dropped database '{db_name}'")
    except Exception as e:
        print(f"\n⚠️ Failed to drop database '{db_name}': {e}")
