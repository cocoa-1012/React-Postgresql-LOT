CALL add_permission(0, 'read tracing record');
CALL add_permission(1, 'write tracing record');
CALL add_permission(2, 'read users own info');
CALL add_permission(3, 'write users own info');
CALL add_permission(4, 'read db1');
CALL add_permission(5, 'write db1');
CALL add_permission(6, 'read anonymized data');
CALL add_permission(7, 'read health data');
CALL add_permission(8, 'write health data');

CALL add_role(0, 'admin');
CALL add_role(1, 'health authority');
CALL add_role(2, 'contact tracer');
CALL add_role(3, 'public user');

CALL add_rolePermission(0, 4);
CALL add_rolePermission(0, 5);
CALL add_rolePermission(0, 0);
CALL add_rolePermission(0, 1);
CALL add_rolePermission(1, 7);
CALL add_rolePermission(1, 8);
CALL add_rolePermission(1, 2);
CALL add_rolePermission(1, 3);
CALL add_rolePermission(2, 0);
CALL add_rolePermission(2, 2);
CALL add_rolePermission(2, 3);
CALL add_rolePermission(3, 2);
CALL add_rolePermission(3, 3);
