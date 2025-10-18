from app.worker.config import WorkerContext, register_handler


@register_handler("handle_neo4j_create_course")
async def handle_neo4j_create_course(payload: dict, ctx: WorkerContext):
    course_id = payload.get("course_id")
    course_name = payload.get("course_name")

    if not course_id:
        raise ValueError(f"Missing course id: {course_id} "
                         f"for graph database sync")

    async with ctx.neo4j_driver.session() as session:
        await session.run(
            "MERGE (c: Course {id: $id, name: $name})",
            id=course_id,
            name=course_name,
        )
    print(f"✅ Course {course_id} synced to graph database")


@register_handler("handle_neo4j_create_knowledge_node")
async def handle_neo4j_create_knowledge_node(payload: dict, ctx: WorkerContext):
    knowledge_node_id = payload.get("knowledge_node_id")
    name = payload.get("name")
    course_id = payload.get("course_id")
    description = payload.get("description")

    if not knowledge_node_id:
        raise ValueError(f"Missing knowledge node id: {knowledge_node_id} "
                         f"for graph database sync")

    async with ctx.neo4j_driver.session() as session:
        await session.run(
            # TODO: rewrite this query
            "MATCH (n) RETURN n",
            id=knowledge_node_id,
        )
    print(f"✅ knowledge node {knowledge_node_id} synced to graph database")


@register_handler("handle_neo4j_create_question")
async def handle_neo4j_create_question(payload: dict, ctx: WorkerContext):
    question_id = payload.get("question_id")
    question_type = payload.get("question_type")
    knowledge_node_id = payload.get("knowledge_node_id")

    if not question_id:
        raise ValueError(f"Missing question id: {question_id} "
                         f"for graph database sync")
    async with ctx.neo4j_driver.session() as session:
        await session.run(
            # TODO: rewrite this query
            "MATCH (n) RETURN n",
            id=question_id,
        )
    print(f"✅ question {question_id} synced to graph database")


@register_handler("handle_neo4j_update_knowledge_node")
async def handle_neo4j_update_knowledge_node(payload: dict, ctx: WorkerContext):
    pass


@register_handler("handle_neo4j_update_question")
async def handle_neo4j_update_question(payload: dict, ctx: WorkerContext):
    pass


@register_handler("handle_neo4j_update_mastery_level")
async def handle_neo4j_update_mastery_level(payload: dict, ctx: WorkerContext):
    pass


@register_handler("handle_neo4j_query_problem")
async def handle_neo4j_query_problem(payload: dict, ctx: WorkerContext):
    pass
