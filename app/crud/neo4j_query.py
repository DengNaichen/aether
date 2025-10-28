

# def fetch_neo4j_knowledge_node_num(course_id):
#     # check if the course is in the neo4j
#     try:
#         # Verify course exists
#         neo.Course.nodes.get(course_id=course_id)
#         # Count knowledge nodes that belong to this course
#         from neomodel import db
#         query = """
#         MATCH (c:Course {course_id: $course_id})<-[:BELONGS_TO]-(k:KnowledgeNode)
#         RETURN COUNT(k) AS count
#         """
#         results, _ = db.cypher_query(query, {"course_id": course_id})
#         return results[0][0] if results else 0
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Course {course_id} not found"
#         )