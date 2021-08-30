-- hypergraphs_schema.sql

CREATE TABLE IF NOT EXISTS json_schemas (
	-- The core of all this database
	payload TEXT NOT NULL,
	-- Due SQLite limitations, a generated column cannot be part
	-- of the primary key
	-- schema_id TEXT GENERATED ALWAYS AS (json_extract(payload, '$.$id')) STORED NOT NULL,
	schema_id VARCHAR(4096) NOT NULL,
	json_schema_id VARCHAR(4096) GENERATED ALWAYS AS (json_extract(payload, '$.$schema')) STORED NOT NULL,
	PRIMARY KEY(schema_id)
);

CREATE TABLE IF NOT EXISTS hypergraph (
	-- The internal unique id of this hypergraph
	h_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	-- When this hypergraph metadata was stored
	stored_at INTEGER NOT NULL ON CONFLICT REPLACE DEFAULT (strftime('%s','now')),
	-- When this hypergraph metadata was stored
	updated_at INTEGER NOT NULL ON CONFLICT REPLACE DEFAULT (strftime('%s','now')),
	-- When was stored this dataset
	-- The annotation payload semantically describes
	-- this hypergraph. It can be any of the accepted
	-- serializations of RDF
	annotation_payload TEXT,
	-- The hypergraph properties are hold here, as a JSON
	payload TEXT NOT NULL,
	-- The hypergraph schema used for the payload
	h_payload_schema_id TEXT GENERATED ALWAYS AS (json_extract(payload, '$._schema')) STORED NOT NULL,
	-- The unique name/id of this hypergraph
	h_payload_id TEXT GENERATED ALWAYS AS (json_extract(payload, '$._id')) STORED NOT NULL,
	-- When was generated this dataset, translated to epoch seconds
	h_payload_generated INTEGER GENERATED ALWAYS AS (strftime('%s', json_extract(payload, '$._generated'))) STORED NOT NULL,
	-- A short name of this hypergraph
	h_payload_name VARCHAR(256) GENERATED ALWAYS AS (json_extract(payload, '$.name')) STORED NOT NULL,
	-- A long description about this hypergraph
	h_payload_desc TEXT GENERATED ALWAYS AS (json_extract(payload, '$.description')) STORED,
	FOREIGN KEY (h_payload_schema_id) REFERENCES json_schemas(schema_id),
	UNIQUE (h_payload_id)
);

CREATE TABLE IF NOT EXISTS node_type (
	-- The internal unique id of this node type
	nt_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	-- The unique name of this node type
	nt_name VARCHAR(256) NOT NULL,
	-- A description about this node type
	nt_desc VARCHAR(4096) NOT NULL,
	-- The schema_id of all the payloads of all
	-- the nodes of this type. It is also reused as URI for RDF
	node_schema_id TEXT NOT NULL,
	-- The annotation payload semantically describes
	-- this type of node. It can be any of the accepted
	-- serializations of RDF
	annotation_payload TEXT,
	-- These are node type metadata
	payload TEXT,
	payload_schema_id TEXT GENERATED ALWAYS AS (json_extract(payload, '$._schema')) STORED,
	FOREIGN KEY (node_schema_id) REFERENCES json_schemas(schema_id),
	FOREIGN KEY (payload_schema_id) REFERENCES json_schemas(schema_id),
	UNIQUE (nt_name)
);

CREATE TABLE IF NOT EXISTS edge_type (
	-- The internal unique id of this edge type
	et_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	-- The unique name of this edge type
	et_name VARCHAR(256) NOT NULL,
	-- A description about this edge type
	et_desc VARCHAR(4096) NOT NULL,
	-- The node type of one of the nodes
	a_nt_id INTEGER NOT NULL,
	-- The node type of the other node
	b_nt_id INTEGER NOT NULL,
	-- Is a directed edge type?
	is_directed INTEGER NOT NULL,
	-- Do nodes of this type of edge fulfil symmetric property?
	is_symmetric INTEGER NOT NULL,
	-- The schema_id of all the payloads of all
	-- the edges of this type. It is also reused as URI for RDF
	edge_schema_id TEXT NOT NULL,
	-- A short name for this weight
	weight_name VARCHAR(256),
	-- A description about this weight
	weight_desc VARCHAR(4096),
	-- The annotation payload semantically describes
	-- this type of edge. It can be any of the accepted
	-- serializations of RDF
	annotation_payload TEXT,
	-- These are edge type metadata, in JSON
	payload TEXT,
	payload_schema_id TEXT GENERATED ALWAYS AS (json_extract(payload, '$._schema')) STORED,
	FOREIGN KEY (edge_schema_id) REFERENCES json_schemas(schema_id),
	FOREIGN KEY (payload_schema_id) REFERENCES json_schemas(schema_id),
	FOREIGN KEY (a_nt_id) REFERENCES node_type(nt_id),
	FOREIGN KEY (b_nt_id) REFERENCES node_type(nt_id),
	UNIQUE (et_name)
);

CREATE TABLE IF NOT EXISTS hyperedge_type (
	-- The internal unique id of this hyperedge type
	het_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	-- The unique name of this edge type
	het_name VARCHAR(256) NOT NULL,
	-- A description about this edge type
	het_desc VARCHAR(4096) NOT NULL,
	-- Is a tuple-like hyperedge? (i.e. number of node types is equal to number of involved nodes)
	is_tuple INTEGER NOT NULL,
	-- Is a directed hyperedge type?
	is_directed INTEGER NOT NULL,
	-- Do nodes of this type of edge fulfil symmetric property?
	is_symmetric INTEGER NOT NULL,
	-- The schema_id of all the payloads of all
	-- the hyperedges of this type. It is also reused as URI for RDF
	hyperedge_schema_id TEXT NOT NULL,
	-- A short name for this weight
	weight_name VARCHAR(256),
	-- A description about this weight
	weight_desc VARCHAR(4096),
	-- The annotation payload semantically describes
	-- this type of edge. It can be any of the accepted
	-- serializations of RDF
	annotation_payload TEXT,
	-- These are hyperedge type metadata, in JSON
	payload TEXT,
	payload_schema_id TEXT GENERATED ALWAYS AS (json_extract(payload, '$._schema')) STORED,
	FOREIGN KEY (hyperedge_schema_id) REFERENCES json_schemas(schema_id),
	FOREIGN KEY (payload_schema_id) REFERENCES json_schemas(schema_id),
	UNIQUE (het_name)
);

CREATE TABLE IF NOT EXISTS hyperedge_type_node_type (
	-- The internal unique id of this pair hyperedge type - node type
	het_nt_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	-- The internal unique id of this hyperedge type
	het_id INTEGER NOT NULL,
	nt_id INTEGER NOT NULL,
	FOREIGN KEY (het_id) REFERENCES hyperedge_type(het_id),
	FOREIGN KEY (nt_id) REFERENCES node_type(nt_id)
);

CREATE TABLE IF NOT EXISTS node (
	-- The internal unique id of this node
	n_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	-- As nodes can appear on more than one graph, they are stored
	-- at the hyper-graph level
	h_id INTEGER NOT NULL,
	-- The id of the node type
	nt_id INTEGER NOT NULL,
	-- The annotation payload semantically describes
	-- this type of node. It can be any of the accepted
	-- serializations of RDF
	annotation_payload TEXT,
	-- payload is JSON formatted
	payload TEXT NOT NULL,
	n_payload_id TEXT GENERATED ALWAYS AS (json_extract(payload, '$._id')) STORED NOT NULL,
	FOREIGN KEY (h_id) REFERENCES hypergraph(h_id),
	FOREIGN KEY (nt_id) REFERENCES node_type(nt_id),
	UNIQUE (n_payload_id, h_id)
);

CREATE TABLE IF NOT EXISTS edge (
	-- The internal unique id of this edge
	e_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	-- Edges relate in a graph nodes of the same or different kind.
	-- In order to ease to select subgraphs from the graph or the
	-- hypergraph, the graphId is declared
	h_id INTEGER NOT NULL,
	et_id INTEGER NOT NULL,
	from_id INTEGER NOT NULL,
	to_id INTEGER NOT NULL,
	-- The annotation payload semantically describes
	-- this type of node. It can be any of the accepted
	-- serializations of RDF
	annotation_payload TEXT,
	-- payload is JSON formatted
	payload TEXT NOT NULL,
	e_payload_f_id TEXT GENERATED ALWAYS AS (json_extract(payload, '$.f_id')) STORED NOT NULL,
	e_payload_t_id TEXT GENERATED ALWAYS AS (json_extract(payload, '$.t_id')) STORED NOT NULL,
	-- In case there is an id for the edge, it should be unique
	e_payload_id TEXT GENERATED ALWAYS AS (json_extract(payload, '$._id')) STORED,
	e_payload_weight REAL GENERATED ALWAYS AS (json_extract(payload, '$.weight')) STORED,
	-- As the graph entry holds this info, it is not needed to have
	-- it repeated on each one of the edge entries
	-- schema_id TEXT GENERATED ALWAYS AS (json_extract(payload, '$._schema')) VIRTUAL NOT NULL,
	-- FOREIGN KEY schema_id REFERENCES json_schemas(schema_id),
	FOREIGN KEY (h_id) REFERENCES hypergraph(h_id),
	FOREIGN KEY (et_id) REFERENCES edge_type(et_id),
	FOREIGN KEY (from_id) REFERENCES node(n_id),
	FOREIGN KEY (to_id) REFERENCES node(n_id),
	UNIQUE (e_payload_id, h_id)
);

CREATE TABLE IF NOT EXISTS hyperedge (
	-- The internal unique id of this hyperedge
	he_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	-- Hyperedges relate in a hypergraph nodes of the same or different kind.
	-- In order to ease to select subhypergraphs from the hypergraph or the
	-- hypergraph, the graphId is declared
	h_id INTEGER NOT NULL,
	het_id INTEGER NOT NULL,
	-- The annotation payload semantically describes
	-- this type of node. It can be any of the accepted
	-- serializations of RDF
	annotation_payload TEXT,
	-- payload is JSON formatted
	payload TEXT NOT NULL,
	weight REAL GENERATED ALWAYS AS (json_extract(payload, '$.weight')) STORED,
	-- As the graph entry holds this info, it is not needed to have
	-- it repeated on each one of the edge entries
	-- schema_id TEXT GENERATED ALWAYS AS (json_extract(payload, '$._schema')) VIRTUAL NOT NULL,
	-- FOREIGN KEY schema_id REFERENCES json_schemas(schema_id),
	FOREIGN KEY (h_id) REFERENCES hypergraph(h_id),
	FOREIGN KEY (het_id) REFERENCES hyperedge_type(het_id)
);

CREATE TABLE IF NOT EXISTS hyperedge_node(
	-- The internal unique id of this hyperedge node pair
	he_n_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	-- The internal unique id of this hyperedge
	he_id INTEGER NOT NULL,
	n_id INTEGER NOT NULL,
	FOREIGN KEY (n_id) REFERENCES node(n_id) ON UPDATE CASCADE ON DELETE CASCADE,
	FOREIGN KEY (he_id) REFERENCES hyperedge(he_id) ON UPDATE CASCADE ON DELETE CASCADE
);