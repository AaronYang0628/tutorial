from pymilvus import MilvusClient

def connect_milvus():
    return MilvusClient(
    uri="http://192.168.31.48:30530",
    token="root:Milvus"
    )

def test_connection():
    client = connect_milvus()
    print(client.list_users())
    print(client.list_databases())
    print(client.list_collections())
    print(client.get_server_version())
    client.close()

if __name__ == '__main__':
    test_connection()