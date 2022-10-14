# Entity Creation



Expanding the current selection of indexed entities is a way of increasing the coverage of queryable network interactions. 

### Implementation


#### Adding the entity schema

in `schema.graphql`:

The graphql schema is amended to include the new entity, with any fields that are required by the future scope of querying. These attributes are preferably only those required inn order to conserve storage.
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

- L0 - Entity is initialised with the `@entity` tag

- L1 - Entity is afforded a unique identifier, ID

- L2-4 - Entity attributes and their types are introduced, some with the `@index` tag to allow more complex querying

- L5-8 - Relevant message, transaction and block are provided to the entity

Updating the system to include these changes can be done by running the following: 
```
yarn codegen
```


#### Implementing the entity handler

in `/src/mappings/your_entity_category/entity_name.ts`

This handler function will be configured to trigger whenever the indexer detects the desired interaction with the entity:

```
0	export async function handleYourEntityName(event: CosmosEvent): Promise<void> {
1		logger.info(`confirmation that your handler is triggered`);
2
3		const id = messageId(event.msg);
4  		const decoded_msg = event.msg.msg.decodedMsg;
5  		const entity_field_a = decoded_msg.entity_field_a;
6  		const entity_field_b = decoded_msg.entity_field_b;
7  		const entity_field_c = decoded_msg.entity_field_c;
8
9  		if (!entity_field_a || !entity_field_b || !entity_field_c) {
10    		logger.warn(`indexing failed ... debug info`)
11    		return
12  	}
13
14    	const entity = TestEntity.create({
15    		id,
16    		entity_field_a,
17    		entity_field_b,
18    		entity_field_c,
19    		messageId: id,
20    		transactionId: event.msg.tx.hash,
21    		blockId: event.msg.block.block.id
22    	});
23	
24		await entity.save();
25	}
```

- L0 - Create an synchronous handler function accepting a `CosmosEvent` as a parameter

- L4-7 - Create a reference to the message relevant to the incoming Event and destructure the message into the desired fields

- L9-12 - Check that these fields have been destructured correctly

- L14-22 - Create a `TestEntity` instance and populate the required fields

- L24 - Save the entity to the database

#### Configuring handler filters

in `project.yaml`:

This example will run the previously instantiated handler whenever the filtering conditions are met - e.g. when an event of type `"event_type"` is captured as triggered by a message with the type `"message_type_url"`

```
0  - handler: handleYourEntityName
1    kind: cosmos/EventHandler
2    filter:
3    	type: "event_type"
4        messageFilter:
5        	type: "message_type_url" 
```

- L0 - Reference the appropriate handler to be called when triggered

- L1 - Define which type of handler this will trigger, in this case an Event handler

- L2-3 - Configure the event filtering for type `"event_type"`

- L4-5 - Configure the relevant message filtering as type `"message_type_url"`


### Testing
The current development is test-driven, as such, the tests within the [`Ledger-SubQuery`](/https://github.com/fetchai/ledger-subquery) repository are based upon a Python `Unittest` suite, running automatically as CI in the form of a Github Action. Each test is designed to be an encapsulated `end-to-end` assertion of each entities' functionality.

The current program flow for each test can be abstracted to the different major parts and services of the system. `CosmPy` is used to interface with the `fetchd` node to construct, configure and interact with messages - which can then be captured and indexed. In order to execute PostgreSQL and GraphQL queries for test value assertion, the `Psycopg` and `GQL` libraries are used.

Entities are tested within their various states between their creation to querying in order to be considered `end-to-end`, or `e2e`, tested. These full `e2e` tests encompass the following:

- Triggering the interaction of focus

- The handler capturing the interaction and creating the relevant entity

- An assertion that the entity has been captured and stored within the database correctly

- Querying to determine if the entity's properties are as expected and not malformed

#### Creating the handler trigger
in `tests/e2e/entities/TestYourEntity.py`:

Each test class relies upon a `SetUp` class method to ensure that the required environment is working. 

The SetUp method of each Entity test class will look similar to the following:

```
0 class TestYourEntity(EntityTest):
1     @classmethod
2     def setUpClass(cls):
3         super().setUpClass()
4         cls.clean_db({"your_entity_table"})
5 		  <trigger entity creation here>
6 		  time.sleep(5)

```


- Starting on *L3* - ensuring that the enviroment for the test suite is initialised by calling the parent class' `SetUp` method - eg. starting psycopg & gql services.
- on *L4* - we truncate the tables, cleaning the database to ensure there are no rows left to interfere with our testing.
- *L5* - Triggering the creation of our entity on this line
- L6 - a 5 second delay in order to allow the indexer time to capture our new entity

#### Psycopg querying

```
0 def test_things(self):
1   db_query = 'SELECT entity_field_a, entity_field_b, ... from test_entities'
2 	entity = self.db_cursor.execute(self.db_query).fetchone()
3 	self.assertIsNotNone(entity, "Assertion failure message")
4 	self.assertEqual(entity[0], "correct value", "Assertion failure message") 
```

- L1 - Set out our PostgreSQL database query to fetch desired columns

- L2 - Fetching the results of the query using the psycopg `db_cursor` database cursor object method `execute` to gather the first row

- L3 - firstly we assert that there is a row gathered, as a non-null output of L2

- L3 - Assert the value of the first column returned of the row, e.g. "entity_field_a". Use the ordinal number of the column in the query as the index.

#### GQL querying

```	
0   test_query = gql(
1       """
2       query getEntity {
3           TestEntities {
4               nodes {
5 				  entity_field_a
6 				  entity_field_b
7    			  entity_field_c
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

- L0-12 - define the GraphQL query for the entity and relevant fields
- L14 - fetch the result of this query using the `gql_client` object method `execute`.
- L16 - assert that the result is not null
- L17 - index the field and assert against the correct value



#### Useful links:
[Ledger-SubQuery](/https://github.com/fetchai/ledger-subquery)

[Cosmpy](/https://github.com/fetchai/cosmpy),
[GQL](/https://github.com/graphql-python/gql),
[Psycopg](/https://www.psycopg.org/),
[Postgraphile](/https://github.com/graphile/postgraphile)