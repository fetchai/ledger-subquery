# Entity Creation

By expanding the group of currently indexable entities we can increase the coverage of queryable network interactions. 

### Implementation


#### Adding the entity schema

Within`schema.graphql`:

The GraphQL schema is amended to include the new entity, with any fields that are required to support new use cases. These attributes are ideally **only those necessary, in order to minimise storage requirements**.
```
0  type TestEntity @entity {
1  		id: ID!
2   	entity_field_a: String! @index
3   	entity_field_b: String! @index
4   	entity_field_c: String!
5   	message: Message!
6   	transaction: Transaction!
7   	block: Block!
8  }
```

- **L0** - Entity is defined as a GraphQL entity with the `@entity` annotation.

- **L1** - TestEntity requires a unique identifier, GraphQL type: ID - this column will be represented by the `text` type in SQL.

- **L2-4** - Required entity attributes and their types are added, some with the `@index` tag to allow faster querying for anticipated use cases.

- **L5-8** - The entities message, transaction and block are related.

Updating the generated code to include these changes can be done by running the following: 
```
yarn codegen
```


#### Implementing the entity handler

Within `/src/mappings/your_entity_category/entity_name.ts`:

By convention, handler functions are organized according to the relevant Cosmos-SDK module to which the entity represents or with which they interact. Exceptions to this convention are appropriate as required.

This handler function will be [configured](#creating-the-handler-trigger) to trigger whenever the indexer detects the targeted interaction:

```
0   export async function handleYourEntityName(event: CosmosEvent): Promise<void> {
1       logger.info(`confirmation that your handler is triggered`);
2
3       const id = `${event.msg.tx.hash}-${event.msg.idx}`;
4       transactionId = event.msg.tx.hash;
5       blockId: event.msg.block.block.id;
6       const decoded_msg = event.msg.msg?.decodedMsg;
7       const entity_field_a = decoded_msg?.entity_field_a;
8       const entity_field_b = decoded_msg?.entity_field_b;
9       const entity_field_c = decoded_msg?.entity_field_c;
10
11      if (!entity_field_a || !entity_field_b || !entity_field_c) {
12    	    logger.warn(`indexing failed ... debug info`);
13    	    return
14      }
15
16      const entity = TestEntity.create({
17    	    id,
18    	    entity_field_a,
19    	    entity_field_b,
20    	    entity_field_c,
21    	    messageId: id,
22    	    transactionId,
23    	    blockId,
24      });
25	
26      await entity.save();
27  }
```

- **L0** - Create an asynchronous handler function accepting a `CosmosEvent` as a parameter. The convention for event-based handlers is in place to ensure we only handle successful transactions - as opposed to message-based handling where an expensive internal completion check must be made.
  - Using the safe navigation operator `?` allows us to reference message values regardless of whether they exist, such as `event.msg?.msg?.decodedMsg?.entity_field_a`, where one or more of the parent structures could be corrupted and halt  the indexer without the operator.
- **L3-9** - Create a reference to the message related to the event and assign variables from the appropriate message fields.

- **L11-14** - Check that these fields are valid, abandoning attempt at indexing the event in the case that any fields are malformed. Allowing the indexer to continue.

- **L16-24** - Create a `TestEntity` instance and populate the required fields.

- **L26** - Save the entity to the database.

#### Configuring handler filters

in `project.yaml`:

This example will run the respective [handler](#implementing-the-entity-handler) whenever the filtering conditions are met - e.g. when an event of type `"event_type"` is captured as triggered by a message with the type `"message_type_url"`

```
0  - handler: handleYourEntityName
1    kind: cosmos/EventHandler
2    filter:
3    	type: "event_type"
4        messageFilter:
5        	type: "message_type_url" 
```

- **L0** - Reference the TypeScript handler function to be called when triggered.

- **L1** - Define which type of handler this will trigger, in this case an Event handler. This will provide the event to the handler as the function signature.

- **L2-3** - Configure the event filtering for type `event_type`.

- **L4-5** - Configure the relevant message filtering as type `message_type_url`.

[Further reading](https://academy.subquery.network/build/manifest/cosmos.html#mapping-handlers-and-filters)

### Testing
The current development is test-driven, as such, the tests within the [`ledger-subquery`](/https://github.com/fetchai/ledger-subquery) repository are based upon a Python `Unittest` suite. This suite is executed within CI in the form of a GitHub Action. Each test is designed to be an encapsulated `end-to-end` assertion of each entities' functionality.

The current program flow for each test can be abstracted to the different major parts and services of the system. `CosmPy` is used to interface with the `fetchd` node to construct and broadcast messages which will then be indexed. In order to execute PostgreSQL and GraphQL queries for test value assertion, the `Psycopg` and `GQL` libraries are used.

Entities are tested within their various states between their creation to querying in order to be considered `end-to-end`, or `e2e`, tested. These full `e2e` tests encompass the following:

- Triggering the interaction of focus.

- The handler capturing the interaction and creating the relevant entity.

- An assertion that the entity has been captured and stored within the database correctly.

- Querying to determine if the entity's properties are as expected and not malformed.

#### Creating the handler trigger
in `tests/e2e/entities/TestYourEntity.py`:

Each test class relies upon a `SetUpClass` class method to ensure the prerequisite initialization and cleanup of the test environment. 

The `SetUpClass` method of each Entity test class will look similar to the following:

```
0 class TestYourEntity(EntityTest):
1     @classmethod
2     def setUpClass(cls):
3         super().setUpClass()
4         cls.clean_db({"your_entity_table"})
5 		  <trigger entity creation here>
6 		  time.sleep(5)

```


- **L3** - Affirm that the environment for the test suite is initialised by calling the parent class' `SetUpClass` method - e.g. setting up psycopg & gql clients.
- **L4** - Truncate the tables, cleaning the database to ensure there are no rows left to interfere with our testing.
- **L5** - Triggering the creation of the entity
- **L6** - 5-second delay providing the indexer time to capture the new entity

#### SQL Database querying

```
0 def test_things(self):
1   db_query = 'SELECT entity_field_a, entity_field_b, ... from test_entities'
2 	entity = self.db_cursor.execute(self.db_query).fetchone()
3 	self.assertIsNotNone(entity, "Assertion failure message")
4 	self.assertEqual(entity[0], "correct value", "Assertion failure message") 
```

- **L1** - Set out a SQL query to fetch the columns corresponding to the fields defined in `schema.graphql`.

- **L2** - Fetch the results of the query using the Psycopg `db_cursor` database cursor method [`execute`](https://www.psycopg.org/docs/usage.html) to return the first row.

- **L3** - Assert that there is a row returned, as a non-null output of **L2**.

- **L3** - Assert the value for the first field of the row, e.g. `entity_field_a`. Use the ordinal number of the column in the query as the index. In practise, this is abstracted within `tests/helpers/field_enums.py` with the use of an `Enum` describing each entity.

#### GQL querying

```	
0   test_query = gql(
1       """
2       query getEntity {
3           TestEntities {
4               nodes {
5                  entity_field_a
6                  entity_field_b
7                  entity_field_c
8               }
9           }
10      }    
11      """
12   )
13
14   result = self.gql_client.execute(test_query)
15   entity = result["TestEntities"]["nodes"]
16   self.assertNotEqual(entity, [], "Assertion error message")
17   self.assertEqual(entity[0]["entity_field_a"], "correct value", "Assertion error message")
```

- **L0-12** - Define the GraphQL query for the entity and relevant fields.
- **L14** - Fetch the result of this query using the `gql_client` object method `execute`.
- **L16** - Assert that the result is not null.
- **L17** - Assert the actual field value against the expected value.

### DB Migrations
It is important to note that updating or adding entities to an existing database will require a migration. 

There is some infrastructure in place to allow complex migrations to be written in either SQL or Typescript using the `graphile-migrate` and `PLV8` plugins for Postgraphile and Postgres, respectively. There is further technical documentation regarding this process [here](https://github.com/fetchai/ledger-subquery#db-migrations).

#### Useful links:
[Ledger-SubQuery](/https://github.com/fetchai/ledger-subquery)

[Cosmpy](/https://github.com/fetchai/cosmpy),
[GQL](/https://github.com/graphql-python/gql),
[Psycopg](/https://www.psycopg.org/),
[Postgraphile](/https://github.com/graphile/postgraphile)