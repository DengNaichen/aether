-- =====================================================
-- Migration: Add topology calculation triggers
-- Description: Automatically recalculate level and dependents_count
--              when prerequisites table changes
-- =====================================================

-- =====================================================
-- Step 1: Core calculation function
-- =====================================================

CREATE OR REPLACE FUNCTION recalculate_graph_topology(target_graph_id UUID)
RETURNS VOID AS $$
BEGIN
    -- Step 1: Reset all nodes to default values first
    UPDATE knowledge_nodes
    SET level = 0, dependents_count = 0
    WHERE graph_id = target_graph_id;

    -- Step 2: Calculate level (topological depth in DAG)
    -- level = 0: nodes with no prerequisites
    -- level = N: max(prerequisite levels) + 1
    WITH RECURSIVE topo_levels AS (
        -- Base case: nodes with no incoming prerequisite edges -> level = 0
        SELECT
            n.id AS node_id,
            0 AS level
        FROM knowledge_nodes n
        WHERE n.graph_id = target_graph_id
          AND NOT EXISTS (
              SELECT 1 FROM prerequisites p
              WHERE p.graph_id = target_graph_id
                AND p.to_node_id = n.id
          )

        UNION ALL

        -- Recursive case: nodes whose prerequisites have been processed
        SELECT
            p.to_node_id AS node_id,
            tl.level + 1 AS level
        FROM prerequisites p
        INNER JOIN topo_levels tl ON p.from_node_id = tl.node_id
        WHERE p.graph_id = target_graph_id
    ),
    -- Take max level for each node (handles multiple prerequisite paths)
    max_levels AS (
        SELECT node_id, MAX(level) AS level
        FROM topo_levels
        GROUP BY node_id
    )
    UPDATE knowledge_nodes n
    SET level = ml.level
    FROM max_levels ml
    WHERE n.id = ml.node_id
      AND n.graph_id = target_graph_id;

    -- Step 3: Calculate dependents_count (how many nodes depend on this node)
    -- This counts all direct and indirect dependents
    WITH RECURSIVE downstream AS (
        -- Base case: direct dependents
        SELECT
            p.from_node_id AS root_node,
            p.to_node_id AS dependent_node
        FROM prerequisites p
        WHERE p.graph_id = target_graph_id

        UNION

        -- Recursive case: dependents of dependents
        SELECT
            d.root_node,
            p.to_node_id AS dependent_node
        FROM downstream d
        INNER JOIN prerequisites p
            ON d.dependent_node = p.from_node_id
           AND p.graph_id = target_graph_id
    ),
    dep_counts AS (
        SELECT root_node, COUNT(DISTINCT dependent_node) AS cnt
        FROM downstream
        GROUP BY root_node
    )
    UPDATE knowledge_nodes n
    SET dependents_count = dc.cnt
    FROM dep_counts dc
    WHERE n.id = dc.root_node
      AND n.graph_id = target_graph_id;

END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Step 2: Trigger functions for each operation type
-- =====================================================

-- Trigger function for INSERT operations
CREATE OR REPLACE FUNCTION trigger_topology_on_insert()
RETURNS TRIGGER AS $$
DECLARE
    affected_graph_id UUID;
BEGIN
    SELECT DISTINCT graph_id INTO affected_graph_id FROM new_table LIMIT 1;

    IF affected_graph_id IS NOT NULL THEN
        PERFORM recalculate_graph_topology(affected_graph_id);
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger function for UPDATE operations
CREATE OR REPLACE FUNCTION trigger_topology_on_update()
RETURNS TRIGGER AS $$
DECLARE
    affected_graph_id UUID;
BEGIN
    SELECT DISTINCT graph_id INTO affected_graph_id FROM new_table LIMIT 1;

    IF affected_graph_id IS NOT NULL THEN
        PERFORM recalculate_graph_topology(affected_graph_id);
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger function for DELETE operations
CREATE OR REPLACE FUNCTION trigger_topology_on_delete()
RETURNS TRIGGER AS $$
DECLARE
    affected_graph_id UUID;
BEGIN
    SELECT DISTINCT graph_id INTO affected_graph_id FROM old_table LIMIT 1;

    IF affected_graph_id IS NOT NULL THEN
        PERFORM recalculate_graph_topology(affected_graph_id);
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Step 3: Create triggers with transition tables
-- =====================================================

-- Drop existing triggers if any
DROP TRIGGER IF EXISTS trg_prerequisites_insert ON prerequisites;
DROP TRIGGER IF EXISTS trg_prerequisites_update ON prerequisites;
DROP TRIGGER IF EXISTS trg_prerequisites_delete ON prerequisites;

-- Create new triggers using transition tables (PostgreSQL 10+)
CREATE TRIGGER trg_prerequisites_insert
AFTER INSERT ON prerequisites
REFERENCING NEW TABLE AS new_table
FOR EACH STATEMENT
EXECUTE FUNCTION trigger_topology_on_insert();

CREATE TRIGGER trg_prerequisites_update
AFTER UPDATE ON prerequisites
REFERENCING NEW TABLE AS new_table
FOR EACH STATEMENT
EXECUTE FUNCTION trigger_topology_on_update();

CREATE TRIGGER trg_prerequisites_delete
AFTER DELETE ON prerequisites
REFERENCING OLD TABLE AS old_table
FOR EACH STATEMENT
EXECUTE FUNCTION trigger_topology_on_delete();

-- =====================================================
-- Step 4: Initialize existing data
-- =====================================================

-- Recalculate topology for all existing graphs
DO $$
DECLARE
    graph_record RECORD;
BEGIN
    FOR graph_record IN SELECT DISTINCT id FROM knowledge_graphs LOOP
        PERFORM recalculate_graph_topology(graph_record.id);
    END LOOP;
END $$;
