import xlrd
from .models import Material


async def parse_mate_data(upload_file):
    file_data = xlrd.open_workbook(file_contents=upload_file.body)
    sheet_table = file_data.sheet_by_index(0)
    total_rows = sheet_table.nrows

    objects = []
    for i in range(1, total_rows):
        row_data = sheet_table.row_values(i)
        objects.append(Material(part_num=row_data[1],
                                mate_model = row_data[2],
                                mate_desc=row_data[3],
                                spec_size=row_data[4],
                                spec_weight=row_data[5],
                                spec_min_qty=row_data[6],
                                spec_max_qty=row_data[7],
                                mate_type=row_data[8],
                                purchase_type=row_data[9],
                                purchase_cycle=row_data[10],
                                safety_stock=row_data[11],
                                safety_lower=row_data[12],
                                ))

    try:
        _ = await Material.bulk_create(objects)
        return True
    except Exception as e:
        print(e)
        return False


async def parse_bom_data(upload_file):
    file_data = xlrd.open_workbook(file_contents=upload_file.body)
    sheet_table = file_data.sheet_by_index(0)
    total_rows = sheet_table.nrows

    return True


async def parse_po_data(upload_file):
    file_data = xlrd.open_workbook(file_contents=upload_file.body)
    sheet_table = file_data.sheet_by_index(0)
    total_rows = sheet_table.nrows

    return True


async def parse_order_data(upload_file):
    file_data = xlrd.open_workbook(file_contents=upload_file.body)
    sheet_table = file_data.sheet_by_index(0)
    total_rows = sheet_table.nrows

    return True
