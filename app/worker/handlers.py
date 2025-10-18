from app.worker.config import WorkerContext, register_handler


@register_handler("handle_neo4j_create_course")
async def handle_neo4j_create_course(payload: dict, ctx: WorkerContext):
    """

    """
    course_id = payload.get("course_id")
    course_name = payload.get("course_name")

    if not course_id:
        raise ValueError(f"Missing course id: {course_id} "
                         f"for graph database sync")

    async with ctx.neo4j_session() as session:
        # Use execute_write to ensure the transaction is committed.
        await session.execute_write(
            lambda tx: tx.run(
                "MERGE (c: Course {id: $id, name: $name})",
                id=course_id,
                name=course_name,
            )
        )
    print(f"✅ Course {course_id} synced to graph database")


@register_handler("handle_neo4j_enroll_a_student_in_a_course")
async def handle_neo4j_enroll_a_student_in_a_course(
        payload: dict,
        ctx: WorkerContext
):
    """

    """
    course_id = payload.get("course_id")
    student_id = payload.get("student_id")
    student_name = payload.get("student_name")

    if not course_id:
        raise ValueError(f"Missing course id: {course_id} ")
    if not student_id:
        raise ValueError(f"Missing student id: {student_id} ")
    if not student_name:
        raise ValueError(f"Missing student name: {student_name} ")

    async with ctx.neo4j_session() as session:
        await session.execute_write(
            lambda tx: tx.run(
                """
                MERGE (u: User {id: $user_id, name: $user_name}),
                MERGE (c: Course {id: $course_id}),
                MERGE(u)-[r:ENROLLED_IN]->(c)
                RETURN count(r) > 0 AS success
                """,
                user_id=student_id,
                user_name=student_name,
                course_id=course_id,
            )
        )
    print("✅ Successfully enrolled student {student_id} in course {course_id} ")


@register_handler("handle_neo4j_create_knowledge_node")
async def handle_neo4j_create_knowledge_node(payload: dict, ctx: WorkerContext):
    knowledge_node_id = payload.get("knowledge_node_id")
    course_id = payload.get("course_id")

    if not knowledge_node_id:
        raise ValueError(f"Missing knowledge node id: {knowledge_node_id} "
                         f"for graph database sync")
    if not course_id:
        raise ValueError(f"Missing course id: {course_id} ")

    async with ctx.neo4j_session() as session:
        await session.execute_write(
            lambda tx: tx.run(
                """
                 MERGE (kn: KnowledgeNode {id: $kn_id})})
                 MERGE (c: Course {id: $course_id})
                 MERGE(kn)-[r:BELONG_TO]->(c)
                 RETURN count(r) > 0 AS success
                """,
                kn_id=knowledge_node_id,
                course_id=course_id,
            )
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
    async with ctx.neo4j_session() as session:
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
