# Android/Room pagination playbook

Use for Android Auto, MediaLibrarySession browsing, large settings/catalog lists, or any Android data
path where the UI/controller provides page/pageSize but the repository may still materialize the
entire dataset.

## End-to-end trace

Trace pagination through the full boundary:

```text
caller page/pageSize
    -> Media3/UI callback
    -> repository/use case
    -> DAO/data source
    -> SQL/query/API limit+offset (or equivalent)
    -> stable ordered result
```

Do not declare a path paginated merely because the final list uses `.take(pageSize)`.

## Query shape

For Room/SQL-backed collections, prefer query-level pagination when the collection can be large:

```sql
... ORDER BY <stable order>
LIMIT :limit OFFSET :offset
```

Use a stable deterministic order. If the existing product order has tie conditions, preserve or make
that order explicit rather than letting pagination introduce duplicates/skips across pages.

For non-SQL stores, use the native bounded retrieval mechanism rather than materializing everything
when one exists.

## Do not paginate everything mechanically

Static roots, tiny fixed menus, or intentionally small generated lists may be clearer and cheaper to
keep in memory. Optimize the data paths whose cardinality can actually grow.

## Preserve the browsing contract

Check:

- parent/child IDs;
- browsable/playable flags;
- sort order;
- root/home virtual folders;
- search results;
- current queue/item identity;
- favorites/download filters;
- empty-state semantics;
- counts when exposed separately.

Avoid N+1 metadata queries introduced by paging.

## Boundary matrix

At minimum test:

- empty dataset;
- one item;
- page 0;
- page 1 / middle page;
- final partial page;
- page beyond end;
- pageSize 1;
- typical pageSize;
- dataset >1000 rows;
- ordering ties;
- no duplicates between adjacent pages;
- concatenated pages equal the reference ordered dataset for the tested fixture.

If the public API defines behavior for invalid page/pageSize values, test those exact boundaries too.
Do not invent semantics absent from the framework/project contract.

## Concurrency and refresh

If the underlying dataset can change while paging:

- identify whether snapshot consistency is required;
- determine whether duplicates/skips across separate requests are acceptable framework behavior;
- avoid pretending offset pagination is snapshot-stable when concurrent writes can reorder data.

Use a stronger paging key/cursor only when the product contract actually requires it and the change
is justified.

## Proof

A DAO unit test proves query semantics. It does not by itself prove that Media3/controller callbacks
propagate page/pageSize correctly. Add the cheapest integration layer that can prove the full changed
contract when that propagation is part of acceptance.
