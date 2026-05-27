# No models — Redis is schema-less
# Key conventions:
#
#   user:counter            → auto-increment counter
#   users:all               → Set of all user IDs
#   user:{id}               → Hash {
#                               email, name, created_at, updated_at,
#                               username?, first_name?, last_name?,
#                               gender?, age?, phone?
#                             }
#
#   product:counter         → auto-increment counter
#   products:all            → Set of all product IDs
#   product:{id}            → Hash {
#                               name, price, created_at, updated_at,
#                               description?, category?, characteristics? (JSON string)
#                             }
#
#   order:counter                    → auto-increment counter
#   orders:all                       → Set of all order IDs
#   orders:user:{user_id}            → Set of order IDs for a specific user
#   order:{id}                       → Hash {
#                                        user_id, status, total_price,
#                                        created_at, updated_at
#                                      }
#   order:{id}:items                 → List of JSON strings, each:
#                                        {"product_id": "...", "quantity": 2}
#   orders:product:{product_id}      → Set of order IDs containing this product
