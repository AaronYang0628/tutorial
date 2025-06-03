from pydoc import cli
from connectionTest import connect_milvus


if __name__ == '__main__':
    client=connect_milvus()

    database_name = "my_database_from_python"

    # create database
    client.create_database(
        db_name=database_name,
        properties={
        "database.replica.number": 2,
        "database.diskQuota.mb":  1024,
        "database.max.collections": 2
    }
    )

    
    print(client.describe_database(database_name))

    client.alter_database_properties(   
        db_name=database_name,
        properties={
        "database.max.collections": 10
    }    
    )

    client.drop_database_properties(
        db_name=database_name,
        property_keys={
            "database.max.collections"
        }
    )

    print(client.describe_database(database_name))

    # drop database
    # client.drop_database(
    #     db_name=database_name
    # )


    client.close()


