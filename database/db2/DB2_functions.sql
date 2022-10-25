CREATE OR REPLACE PROCEDURE add_tracingRecord
(recordID INT, tokenID MACADDR, record_time TIMESTAMP, location VARCHAR)
AS $$
BEGIN
  INSERT INTO TracingRecords (traceRecordId, tokenID, time, location) VALUES (recordID, tokenID, record_time, location);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE PROCEDURE edit_tracingRecord
(recordID INT, tokenID MACADDR, record_time TIMESTAMP, location VARCHAR)
AS $$
BEGIN
  UPDATE TracingRecords SET tokenID = tokenID, time = record_time, location = location WHERE traceRecordId = recordID;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE PROCEDURE remove_tracingRecord
(recordID INT)
AS $$
BEGIN
  DELETE FROM TracingRecords WHERE traceRecordId = recordID;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE PROCEDURE add_token 
(id MACADDR, assignedDate DATE)
AS $$
BEGIN
  INSERT INTO Tokens (tid, assignedDate, status) VALUES (id, assignedDate, 1);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE PROCEDURE deactivate_token (id MACADDR)
AS $$
BEGIN
  UPDATE Tokens SET status = 0 WHERE tid = id;
END;
$$ LANGUAGE plpgsql;

--Functions for retrieving data
--Functions for admin & contact tracers;
DROP FUNCTION IF EXISTS get_all_token_data();
DROP FUNCTION IF EXISTS get_all_tracing_data();

CREATE OR REPLACE FUNCTION get_all_token_data()
RETURNS SETOF Tokens AS $$
BEGIN
  RETURN QUERY (SELECT * FROM Tokens);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_all_tracing_data()
RETURNS SETOF TracingRecords AS $$
BEGIN
  RETURN QUERY (SELECT * FROM TracingRecords);
END;
$$ LANGUAGE plpgsql;
