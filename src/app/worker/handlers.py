from src.app.worker.worker_context import WorkerContext, register_handler


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
