import pymysql
import os

class Database:
    def get_db_connection(self):
        """Create and return a new database connection."""
        return pymysql.connect(host=os.getenv("HOST_NAME"),
                               user=os.getenv("USER_NAME"),
                               password=os.getenv("PASSWORD"),
                               db=os.getenv("DBNAME"),
                               cursorclass=pymysql.cursors.DictCursor)
        
    def checkConnection(self):
        """Check the database connection by querying database tables."""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s LIMIT 1", (os.getenv('DBNAME'),))
                    if cursor.fetchone():
                        print("Database connected!")
                        return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
        return False

    def select(self, query, args=None):
        """Execute a SELECT query."""
        with self.get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, args)
                return cursor.fetchall()

    def insert(self, table_name, **data):
        """Insert a record into the database."""
        with self.get_db_connection() as conn:
            with conn.cursor() as cursor:
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['%s'] * len(data))
                sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, tuple(data.values()))
                conn.commit()
                return cursor.lastrowid

    def Update(self, table_name, where, **data):
        """Update records in the database."""
        with self.get_db_connection() as conn:
            with conn.cursor() as cursor:
                set_clause = ', '.join([f"{key} = %s" for key in data])
                sql = f"UPDATE {table_name} SET {set_clause} WHERE {where}"
                cursor.execute(sql, tuple(data.values()))
                conn.commit()

    def delete(self, table_name, where, **args):
        """Delete records from the database."""
        with self.get_db_connection() as conn:
            with conn.cursor() as cursor:
                sql = f"DELETE FROM {table_name} WHERE {where}"
                cursor.execute(sql, tuple(args.values()))
                conn.commit()

    def migrate_db(self, path_to_sql_file):
        """Execute SQL statements stored in a file."""
        with self.get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Read the SQL file
                with open(path_to_sql_file) as f:
                    sql_script = f.read()
                
                # Execute each statement in the file
                for statement in sql_script.split(';'):
                    if statement.strip():
                        cursor.execute(statement)
                
                conn.commit()
                print("Database migration completed successfully.")

# Helper function to write data to a file (used in the update method for logging)
def write_to_file(data, filename="output.txt"):
    with open(filename, "w") as f:
        f.write(data)
