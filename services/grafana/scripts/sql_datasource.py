from typing import Any, Optional, Self

from grafana_foundation_sdk.cog import builder
from grafana_foundation_sdk.cog import runtime as cogruntime
from grafana_foundation_sdk.cog import variants as cogvariants
from grafana_foundation_sdk.models.dashboard import DataSourceRef


class PostgresQuery(cogvariants.Dataquery):
    hide: Optional[bool]
    query_type: Optional[str]
    with_transforms: bool
    datasource: Optional[DataSourceRef]

    def __init__(
        self,
        raw_sql: Optional[str] = None,
        ref_id: str = "A",
        format: str = "time_series",
        datasource: Optional[DataSourceRef] = None,
    ):
        self.ref_id = ref_id
        self.raw_sql = raw_sql
        self.format = format
        self.datasource = datasource

    def to_json(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "refId": self.ref_id,
            "rawSql": self.raw_sql,
            "rawQuery": True,
            "format": self.format,
        }

        if self.datasource is not None:
            payload["datasource"] = self.datasource.to_json()

        return payload

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        args: dict[str, Any] = {}

        if "rawSql" in data:
            args["raw_sql"] = data["rawSql"]
        if "refId" in data:
            args["ref_id"] = data["refId"]
        if "format" in data:
            args["format"] = data["format"]
        if "datasource" in data:
            args["datasource"] = DataSourceRef.from_json(data["datasource"])

        return cls(**args)


def postgres_query_variant_config() -> cogruntime.DataqueryConfig:
    return cogruntime.DataqueryConfig(
        identifier="postgres-query",
        from_json_hook=PostgresQuery.from_json,
    )


class PostgresQueryBuilder(builder.Builder[PostgresQuery]):
    __internal: PostgresQuery

    def __init__(self):
        self.__internal = PostgresQuery()

    def build(self) -> PostgresQuery:
        return self.__internal

    def query(self, query: str) -> Self:
        self.__internal.raw_sql = query
        return self

    def ref_id(self, ref_id: str) -> Self:
        self.__internal.ref_id = ref_id
        return self

    def format(self, format: str) -> Self:
        self.__internal.format = format
        return self

    def datasource(self, datasource: DataSourceRef) -> Self:
        self.__internal.datasource = datasource
        return self
