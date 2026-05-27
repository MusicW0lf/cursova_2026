# No ORM models — pure Cypher, nodes defined implicitly in queries
# Node labels: User, Product, Order
# Order has relationships: (:Order)-[:BY]->(:User), (:Order)-[:CONTAINS]->(:Product)
