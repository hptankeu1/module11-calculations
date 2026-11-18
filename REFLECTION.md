# Module 11 Reflection: Calculation Model & Validation

## What I built
I added a `Calculation` model to the Module 10 user app. It uses SQLAlchemy with a foreign key
to `users`. I also wrote Pydantic schemas (`CalculationCreate`, `CalculationRead`) and a
factory that picks the arithmetic logic for each type. There are 107 unit and integration tests,
and the integration tests run against PostgreSQL in GitHub Actions before the image is
scanned and pushed to Docker Hub.

## Key decisions
- **Store vs. compute the result.** I chose to store `result`. A calculation is a record of
  something the user did, so it should not change on its own. Storing it also makes reads
  cheap and allows sorting or filtering by result later. The cost is that the value could go
  stale if `a`, `b` or `type` are edited, so I added `recompute()` for the Edit route in Module 12.
- **Validation in layers.** Pydantic validates at the API boundary. SQLAlchemy `@validates`
  hooks catch invalid values when code builds a model directly. Postgres constraints (native
  enum, NOT NULL, FK with `ON DELETE CASCADE`) are the last line of defense. Each layer is
  covered by its own tests.
- **Factory pattern.** Mapping `CalculationType → Operation` class removed the `if/elif` chain
  and makes the code open for extension. A test registers a custom operation to prove this.

## Challenges and how I solved them
1. **Enum storage.** By default SQLAlchemy stores the enum member *name* (`ADD`), not the value
   (`Add`). I used `values_callable` so the database stores the same readable string that
   clients send. An integration test reads the raw column with SQL to confirm it.
2. **Validator order on the model.** The zero-divisor check depends on both `b` and `type`.
   SQLAlchemy runs `@validates` in whatever order the attributes are assigned, so a check on
   `b` alone missed `Calculation(b=0, type="Divide")`. I added the check to both validators
   and wrote a parametrized test for both orders.
3. **Booleans as numbers.** `True` is an `int` in Python, so Pydantic happily turned it into
   `1.0`. I added a `mode="before"` validator to reject booleans. I also reject `NaN` and
   infinity, which Postgres would store but which make no sense for a calculator.
4. **Test isolation with commits.** My CRUD helpers call `commit()`, which would normally leave
   data behind between tests. I wrapped each test in an outer transaction and used SQLAlchemy 2's
   `join_transaction_mode="create_savepoint"`, so commits become savepoints and everything is
   rolled back at the end.
5. **Stale objects in the session.** A cascade-delete test failed even though Postgres had
   deleted the row, because the session still had the object cached in its identity map.
   Clearing the session before re-querying fixed it and reminded me that integration tests
   need to read from the database, not from the cache.

## What I learned
- How Pydantic schemas and ORM models split the work: schemas shape and validate data at the
  edges, and models describe how data is stored.
- Why running integration tests against the *same* database engine as production matters.
  SQLite would not have caught the enum or cascade behavior.
- How a CI pipeline gates deployment: tests → image scan → push, so a broken or vulnerable
  image never reaches Docker Hub.

## Next steps (Module 12)
Add the BREAD routes (`/calculations`), with the authenticated user's ID supplying `user_id`
and `CalculationRead` as the response model.
