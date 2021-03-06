import logging

from mysql2ch.factory import Global

logger = logging.getLogger("mysql2ch.replication")


def make_etl(args):
    schema = args.schema
    tables = args.tables
    renew = args.renew
    etl_full(schema, tables, renew)


def etl_full(schema, tables, renew=False):
    reader = Global.reader
    writer = Global.writer
    settings = Global.settings

    if not tables:
        tables = Global.settings.schema_table.get(schema)
    else:
        tables = tables.split(",")
    for table in tables:
        pk = reader.get_primary_key(schema, table)
        if not pk:
            logger.warning(f"No pk found in {schema}.{table}, skip")
            continue
        elif isinstance(pk, tuple):
            pk = f"({','.join(pk)}"
        if renew:
            drop_sq = f"drop table {schema}.{table}"
            try:
                writer.execute(drop_sq)
                logger.info(f"drop table success:{schema}.{table}")
            except Exception as e:
                logger.warning(f"Try to drop table {schema}.{table} fail")
        sql = f"CREATE TABLE {schema}.{table} ENGINE = MergeTree ORDER BY {pk} AS SELECT * FROM mysql('{settings.mysql_host}:{settings.mysql_port}', '{schema}', '{table}', '{settings.mysql_user}', '{settings.mysql_password}')"
        writer.execute(sql)
        writer.fix_table_column_type(reader, schema, table)
        logger.info(f"etl success:{schema}.{table}")
