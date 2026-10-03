/*Find categories that have both a parent category and at least one child category using the self-referencing category relationship.*/
SELECT DISTINCT
    c.category_id,
    c.category_name,
    c.parent_category_id
FROM category c
JOIN category child
    ON child.parent_category_id = c.category_id
WHERE c.parent_category_id IS NOT NULL;