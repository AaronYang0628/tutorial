package org.example;
import io.milvus.v2.client.MilvusClientV2;
import io.milvus.v2.client.ConnectConfig;
import io.milvus.v2.service.database.request.*;

public class Main {

  public static void main(String[] args) {
    ConnectConfig config = ConnectConfig.builder()
            .uri("http://192.168.31.48:30530")
            .token("root:Milvus")
            .build();
    MilvusClientV2 client = new MilvusClientV2(config);


//    CreateDatabaseReq createDatabaseReq = CreateDatabaseReq.builder()
//            .databaseName("my_database_1")
//            .build();
//    client.createDatabase(createDatabaseReq);
  }
}