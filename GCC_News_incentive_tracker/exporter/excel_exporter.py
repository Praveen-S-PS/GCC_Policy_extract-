from openpyxl import Workbook


class ExcelExporter:

    @staticmethod
    def export(records):

        wb = Workbook()

        ws = wb.active

        ws.title = "GCC Incentives"

        headers = [

            "Title",
            "Country",
            "State",
            "Category",
            "Policy Type",
            "Incentive Type",
            "Jobs",
            "Investment",
            "Source",
            "Website",
            "Published Date"
        ]

        ws.append(headers)

        for record in records:

            ws.append([

                record[0],
                record[1],
                record[2],
                record[3],
                record[4],
                record[5],
                record[6],
                record[7],
                record[8],
                record[9],
                record[10]
            ])

        wb.save(
            "output/gcc_tracker.xlsx"
        )