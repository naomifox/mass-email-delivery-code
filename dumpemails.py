import web

from config import db

def doit(district):
    q = db.query("select first_name, last_name, address1, address2, city, state, postal, f.value as comment from core_user u join core_action a on (a.user_id = u.id and (a.page_id = 164 or a.page_id = 163 or a.page_id = 160 or a.page_id = 158 or a.page_id = 157 or a.page_id = 153 or a.page_id = 149 or a.page_id = 148)) join core_actionfield f on (f.parent_id = a.id and f.name = 'comment' ) join core_location l on (l.user_id = u.id) where l.us_district = $district", vars=dict(district=district))
    
    fh = file(district + '.txt', 'w')
    
    for r in q:
        if r.address2: r.address2 = '\n' + r.address2
        fh.write(u'{first_name} {last_name}\n{address1}{address2}\n{city}, {state} {postal}\n\n{comment}\n\n\n'.format(**r).encode('utf8'))


if __name__ == "__main__":
    judiciary = ['TX_21', 'MI_14', 'WI_05', 'CA_28', 'NC_06', 'NY_08', 'CA_24', 'VA_03', 'VA_06', 'CA_03', 'CA_16', 'OH_01', 'TX_18', 'CA_49', 'CA_35', 'IN_06', 'TN_09', 'VA_04', 'GA_04', 'IA_05', 'AZ_02', 'IL_05', 'TX_01', 'CA_32', 'OH_04', 'FL_19', 'TX_02', 'CA_39', 'UT_03', 'AR_02', 'PA_10', 'SC_04', 'FL_12', 'FL_24', 'AZ_03', 'NV_02']
    for district in judiciary:
        doit(district)