from google.cloud import bigquery
from metabeaver.GoogleCloudPlatform.BigQuery.TableManagement import create_schema, create_bigquery_table
from metabeaver.Formatting.printControl import conditional_print as cprint

def append_to_bigquery_table(uploadArgs, items_to_append):

    # Get variables packaged in the controlFile
    # Everything to define the target table
    credentials = uploadArgs[0]
    project_id = uploadArgs[1]
    table_set = uploadArgs[2]
    table_name = uploadArgs[3]
    # Everything to define the table column names
    fieldValues = uploadArgs[4]
    cprint('Got upload variables.')

    cprint('Length of items to append was: ')
    cprint(len(items_to_append))
    if len(items_to_append) == 6:
        items_to_append[2] = repr(items_to_append[2])
        items_to_append[3] = repr(items_to_append[3])

    # Check if the table exists
    client = bigquery.Client(project=project_id, credentials=credentials)
    table_id = f"{project_id}.{table_set}.{table_name}"
    cprint('Got client')
    cprint('Table id is:' + table_id)
    table = None
    try:
        table = client.get_table(table_id)
    except Exception as e:
        cprint("Failed to get table: " + table_id)

    # Generate the schema and create the BigQuery tables
    try:
        cprint('Creating schema...')
        schema = create_schema(items_to_append, fieldValues)
    except:
        cprint('Failed to create schema!')

    # Only create the table if it does not exist
    if not table:
        try:
            cprint('Creating table for the first time...')
            table = create_bigquery_table(credentials, project_id, table_set, table_name, schema)
            cprint('Created table!')
        except Exception as e:
            cprint(str(e))
            cprint('Failed to create table')

    # Insert everything in items_to_append as a new row
    row = {name: value for name, value in zip(fieldValues, items_to_append)}
    errors = client.insert_rows_json(table, [row])
    if errors:
        cprint("Failed to insert the row:")
        cprint(errors)
    else:
        cprint("Row inserted successfully.")


# Tries to upload some data to a BigQuery table, based on project, tableset, tablename and instantiated credentials
def toGoogleBigQuery(projectIdentity, tableSet, tableName, credentials, row):

    client = bigquery.Client(credentials=credentials, project=projectIdentity)

    table_ref = client.dataset(tableSet).table(tableName)
    table = client.get_table(table_ref)

    errors = client.insert_rows(table, [row])
    if errors:
        cprint(f"Encountered errors while inserting rows: {errors}")
        return False
    else:
        cprint("Row successfully inserted")
        return True
