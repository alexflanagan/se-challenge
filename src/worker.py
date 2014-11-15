#!venv/bin/python
# -*- coding: utf-8 -*-

import os
import psycopg2
import urlparse


# There is no reason for this to be an object. It's essentially
# just a big function call, but what it does is connect to the
# database, upload the csv, and then pull it back down in the
# format we want (this is called 'Worker', because really
# this should all be done async, which is also where fleshing
# this out into a real object would be useful).
class DataWorker:
    resultMarkup = "<div>No results.</div>"

    def __init__(self, filehandle, encoding="utf-8"):
        # Parse out the environment variable
        # URL and build a Postgres connection..
        urlparse.uses_netloc.append("postgres")
        url = urlparse.urlparse(os.environ["DATABASE_URL"])

        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )

        cursor = conn.cursor()

        # For debugging: drop the table to clean up before creating it.
        # cursor.execute("DROP TABLE IF EXISTS csvstore")

        # Set up the table if it's not already there.
        sql = ''' CREATE TABLE IF NOT EXISTS csvstore
            (entry_date date, category varchar,
            employee_name varchar, employee_address varchar,
            expense_description varchar, pretax_amount money,
            tax_name varchar, tax_amount money) '''

        cursor.execute(sql)

        # Query the CSV file and insert it into the db.
        sql = ''' SET datestyle = 'ISO, MDY';
            COPY csvstore (entry_date,
                category,
                employee_name,
                employee_address,
                expense_description,
                pretax_amount,
                tax_name,
                tax_amount)
            FROM STDIN WITH CSV HEADER '''

        cursor.copy_expert(sql, filehandle)

        # Select our view of the data out grouped and
        # ordered by month out of the database.
        sql = ''' SELECT date_trunc('month', entry_date) AS month,
                sum (pretax_amount) as pretax_subtotal,
                sum (tax_amount) as tax_subtotal,
                sum (pretax_amount - tax_amount) as posttax_subtotal
            FROM csvstore
            GROUP BY month ORDER BY month
        '''

        cursor.execute(sql)

        # Now that we've blocked all this time, the payoff:
        # translate the db's version of the CSV into markup.
        self.resultMarkup = '''<tr>
            <td>Month</td>
            <td>Pretax</td>
            <td>Tax</td>
            <td>After Tax</td>
        </tr>'''

        # Alternate adding the highlight to rows.
        highlight = True

        for row in cursor.fetchall():
            # Pull out the info.
            date, pretax, tax, posttax = row

            # Generate the TR tag with highlighting.
            rowMarkup = ('<tr %s>' %
                         ("class='highlight'" if highlight else ''))

            # Add the rest of the row data.
            self.resultMarkup += rowMarkup + '''
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
            </tr>
            ''' % (date.strftime("%B, %Y"), pretax, tax, posttax)

            # Switch the highlight for the new iteration.
            highlight = not highlight

        # Wrap it all up in a table tag.
        self.resultMarkup = "<table>%s</table>" % self.resultMarkup

        # Clean up our cusor and db connection.
        conn.commit()
        cursor.close()
        conn.close()

    # Accessor for the markup data.
    def result(self):
        return self.resultMarkup
