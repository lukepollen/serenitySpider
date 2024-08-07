import pandas_gbq
from google.cloud import bigquery

from metabeaver.GoogleCloudPlatform.BigQuery.TableManagement import create_schema, create_bigquery_table
from metabeaver.OperationBeaver.logCollector.defaultLogger import Logger

# Append data to a BigQuery table, if it exists. Create the table if it does not exist for IO.
def append_to_bigquery_table(uploadArgs, items_to_append):
    credentials = uploadArgs[0]
    project_id = uploadArgs[1]
    table_set = uploadArgs[2]
    table_name = uploadArgs[3]
    fieldValues = uploadArgs[4]

    logger = Logger()
    logger.log('Got upload variables.')
    logger.log('Length of items to append was: ')
    logger.log(len(items_to_append))

    if len(items_to_append) == 6:
        items_to_append[2] = repr(items_to_append[2])
        items_to_append[3] = repr(items_to_append[3])

    client = bigquery.Client(project=project_id, credentials=credentials)
    table_id = f"{project_id}.{table_set}.{table_name}"
    logger.log('Got client')
    logger.log('Table id is:' + table_id)

    # Attempt to retrieve the table
    try:
        table = client.get_table(table_id)
        logger.log('Table exists.')
    except:
        logger.log(f"Table {table_id} not found. Creating a new one.")

        # Generate schema
        try:
            logger.log('Creating schema...')
            schema = create_schema(items_to_append, fieldValues)
            logger.log('Schema created successfully.')
        except Exception as e:
            logger.log(f'Failed to create schema! Error: {e}')
            return

        # Create the table
        try:
            logger.log('Creating table for the first time...')
            table = create_bigquery_table(client, table_set, table_name, schema)
            logger.log('Created table!')
        except Exception as e:
            logger.log(f'Failed to create table. Error: {e}')
            return

    # Insert rows into the table
    if table:
        try:
            row = {name: value for name, value in zip(fieldValues, items_to_append)}
            errors = client.insert_rows_json(table, [row])
            if errors:
                logger.log("Failed to insert the row:")
                logger.log(errors)
            else:
                logger.log("Row inserted successfully.")
        except Exception as e:
            logger.log(f'Failed to insert row. Error: {e}')
    else:
        logger.log('Table object is None, cannot insert rows.')

# Append data to a BigQuery table, if it exists. Create the table if it does not exist for IO.
def append_set_to_bigquery_table(uploadArgs, items_to_append):

    # Get the authentication details we specified.
    credentials = uploadArgs[0]
    project_id = uploadArgs[1]
    table_set = uploadArgs[2]
    table_name = uploadArgs[3]
    table_id = f"{project_id}.{table_set}.{table_name}"

    # Instantiate a client object for appending links to bigquery
    client = bigquery.Client(project=project_id, credentials=credentials)

    logger = Logger()
    logger.log('Got upload variables.')
    logger.log('Length of items to append was: ')
    logger.log(len(items_to_append))

    # Attempt to retrieve the table
    try:
        table = client.get_table(table_id)
        logger.log(f'{table} exists.')
    except:
        logger.log(f"Table {table_id} not found. Creating a new one.")

        # Generate schema
        try:
            logger.log('Creating schema...')
            schema = create_schema(items_to_append.iloc[0].tolist(), ['Date', 'Time', 'Link'])
            logger.log('Schema created successfully.')
        except Exception as e:
            logger.log(f'Failed to create schema! Error: {e}')
            return

        # Create the table
        try:
            logger.log('Creating table for the first time...')
            table = create_bigquery_table(client, table_set, table_name, schema)
            logger.log('Created table!')
        except Exception as e:
            logger.log(f'Failed to create table. Error: {e}')
            return

    # Insert rows into the table
    try:
        #items_to_append.to_gbq(destination_table=f'{table_set}.{table_name}',
        #          project_id=project_id,
        #          if_exists='append',
        #          credentials=credentials)
        
        pandas_gbq.to_gbq(
            items_to_append,
            f'{table_set}.{table_name}',
            project_id=project_id,
            if_exists='append',
            credentials=credentials,
        )

    except Exception as e:
        print('Could not upload link data!')
        print(str(e))


# Tries to upload some data to a BigQuery table, based on project, tableset, tablename and instantiated credentials
def toGoogleBigQuery(projectIdentity, tableSet, tableName, credentials, row):

    # Try to insert rows into a Google BigQuery table.
    try:
        client = bigquery.Client(credentials=credentials, project=projectIdentity)
        table_ref = client.dataset(tableSet).table(tableName)
        table = client.get_table(table_ref)

        errors = client.insert_rows(table, [row])
        if errors:
            logger.log(f"Encountered errors while inserting rows: {errors}")
            return False
        else:
            logger.log("Row successfully inserted")
            return True
    except Exception as e:
        logger.log(f'Failed to insert row to Google BigQuery. Error: {e}')
        return False


# Tries to upload some data to a BigQuery table, based on project, tableset, tablename and instantiated credentials
def toGoogleBigQuery(projectIdentity, tableSet, tableName, credentials, row):

    # Try to insert rows into a Google BigQuery table.
    try:
        client = bigquery.Client(credentials=credentials, project=projectIdentity)
        table_ref = client.dataset(tableSet).table(tableName)
        table = client.get_table(table_ref)

        errors = client.insert_rows(table, [row])
        if errors:
            logger.log(f"Encountered errors while inserting rows: {errors}")
            return False
        else:
            logger.log("Row successfully inserted")
            return True
    except Exception as e:
        logger.log(f'Failed to insert row to Google BigQuery. Error: {e}')
        return False