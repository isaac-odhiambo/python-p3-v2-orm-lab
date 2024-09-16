from __init__ import CURSOR, CONN

class Review:
    all = {}

    def __init__(self, year, summary, employee_id, id=None):
        self.id = id
        self.year = self.validate_year(year)
        self.summary = self.validate_summary(summary)
        self._employee_id = self.validate_employee_id(employee_id)  # Use a private attribute for validation

    def __repr__(self):
        return (
            f"<Review {self.id}: {self.year}, {self.summary}, "
            f"Employee: {self._employee_id}>"
        )

    @property
    def employee_id(self):
        return self._employee_id

    @employee_id.setter
    def employee_id(self, value):
        self._employee_id = self.validate_employee_id(value)

    @classmethod
    def create_table(cls):
        """Create a new table to persist the attributes of Review instances."""
        sql = """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY,
                year INT,
                summary TEXT,
                employee_id INTEGER,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        """
        CURSOR.execute(sql)
        CONN.commit()

    @classmethod
    def drop_table(cls):
        """Drop the table that persists Review instances."""
        sql = "DROP TABLE IF EXISTS reviews;"
        CURSOR.execute(sql)
        CONN.commit()

    def save(self):
        """Insert a new row or update an existing one based on the ID."""
        if self.id is None:
            # Insert new review record
            CURSOR.execute(
                "INSERT INTO reviews (year, summary, employee_id) VALUES (?, ?, ?)",
                (self.year, self.summary, self._employee_id)
            )
            self.id = CURSOR.lastrowid
            Review.all[self.id] = self
        else:
            # Update existing record
            self.update()

        CONN.commit()

    @classmethod
    def create(cls, year, summary, employee_id):
        """Create a new Review instance, save it to the DB, and return the instance."""
        review = cls(year, summary, employee_id)
        review.save()
        return review

    @classmethod
    def instance_from_db(cls, row):
        """Return a Review instance from a database row."""
        if row[0] in cls.all:
            # Existing instance in the cache
            review = cls.all[row[0]]
            # Ensure attributes match row values
            review.year = row[1]
            review.summary = row[2]
            review._employee_id = row[3]
        else:
            # New instance
            review = cls(row[1], row[2], row[3], row[0])
            cls.all[review.id] = review
        return review

    @classmethod
    def find_by_id(cls, id):
        """Return a Review instance by its database ID."""
        CURSOR.execute("SELECT * FROM reviews WHERE id = ?", (id,))
        row = CURSOR.fetchone()
        if row:
            return cls.instance_from_db(row)
        else:
            return None

    def update(self):
        """Update the table row corresponding to the current Review instance."""
        CURSOR.execute(
            "UPDATE reviews SET year = ?, summary = ?, employee_id = ? WHERE id = ?",
            (self.year, self.summary, self._employee_id, self.id)
        )
        CONN.commit()

    def delete(self):
        """Delete the table row corresponding to the current Review instance."""
        CURSOR.execute("DELETE FROM reviews WHERE id = ?", (self.id,))
        del Review.all[self.id]
        self.id = None
        CONN.commit()

    @classmethod
    def get_all(cls):
        """Return a list of Review instances for every record in the database."""
        CURSOR.execute("SELECT * FROM reviews")
        rows = CURSOR.fetchall()
        return [cls.instance_from_db(row) for row in rows]

    # Validation methods for year, summary, and employee_id properties
    @staticmethod
    def validate_year(year):
        """Validate that the year is an integer and >= 2000."""
        if not isinstance(year, int):
            raise ValueError("Year must be an integer.")
        if year < 2000:
            raise ValueError("Year must be greater than or equal to 2000.")
        return year

    @staticmethod
    def validate_summary(summary):
        """Validate that the summary is not empty."""
        if not summary or len(summary) == 0:
            raise ValueError("Summary cannot be empty.")
        return summary

    @staticmethod
    def validate_employee_id(employee_id):
        """Validate that the employee_id references a valid employee."""
        if not isinstance(employee_id, int):
            raise ValueError("Employee ID must be an integer.")
        # Check if employee_id exists in the employees table
        CURSOR.execute("SELECT 1 FROM employees WHERE id = ?", (employee_id,))
        if CURSOR.fetchone() is None:
            raise ValueError("Employee ID must reference an existing employee.")
        return employee_id
