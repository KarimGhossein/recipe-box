"""Rebuild Recipe Box's NUTRI_DB from USDA SR28 (= SR Legacy).

Usage (from the repo root):
  npm pack fda-nutrient-database@1.0.2 && mkdir -p tools/usda/sr28 && tar -xzf fda-nutrient-database-1.0.2.tgz -C tools/usda/sr28
  python3 tools/usda/build_nutri_db.py          # writes tools/usda/out/{nutri_db.js,audit.csv,sources.json}
Then paste nutri_db.js over `const NUTRI_DB = {...};` in app/index.html, update NUTRI_SOURCE from sources.json,
and run `npm test`. To add an ingredient: add it to ADD below with its NDB number (search FOOD_DES.txt).

Rule: each entry describes the ingredient as a recipe measures it -
meat/fish/produce raw, grains/pasta/lentils dry, beans canned or cooked - with
"cooked ..." entries for grains people measure after cooking.
Output: nutri_db.js snippet + audit.csv (old vs new) + sources.json
"""
import json, re, sys, csv
import os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
OUT = os.path.join(HERE, 'out'); os.makedirs(OUT, exist_ok=True)
from sr28 import load
from appdb import load_appdb

rows, desc = load()
old, old_extra = load_appdb(os.path.join(HERE, '..', '..', 'app', 'index.html'))

# key -> (NDB, {portion overrides}) ; None = no USDA match, keep current values (estimate)
P = lambda **k: k
MAP = {
 'water': ('14555', {}),
 'chicken breast': ('05062', P(unit=170)), 'chicken thigh': ('05096', P(unit=110)),
 'ground beef': ('23567', {}), 'ground turkey': ('05305', {}),
 'bacon': None,  # cooked slice values (rendered fat is discarded); unit = 1 cooked slice
 'salmon': ('15236', P(unit=170)), 'shrimp': ('15270', P(unit=8)),
 'egg': ('01123', P(unit=50)), 'tofu': ('16427', {}), 'milk': ('01077', {}),
 'heavy cream': ('01053', {}), 'butter': ('01001', {}), 'cheddar cheese': ('01009', {}),
 'mozzarella cheese': ('01029', P(cup=113)), 'parmesan cheese': ('01032', {}),
 'cream cheese': ('01017', {}), 'greek yogurt': ('01256', {}), 'sour cream': ('01056', {}),
 'all-purpose flour': ('20081', P(cup=125, tbsp=8, tsp=2.6)), 'whole wheat flour': ('20080', {}),
 'white rice': ('20044', P(cup=185, tbsp=12, tsp=4)), 'brown rice': ('20036', P(cup=185, tbsp=12, tsp=4)),
 'pasta': ('20120', P(cup=100, unit=0)), 'bread': ('18069', P(unit=28)),
 'oats': ('08120', P(cup=81, tbsp=5, tsp=1.7)), 'quinoa': ('20035', P(cup=170, tbsp=11, tsp=3.5)),
 'panko breadcrumbs': ('18079', P(cup=60, tbsp=4, tsp=1.3)),
 'tortilla': ('18364', P(unit=48)),
 'black beans': ('16315', P(cup=172)), 'chickpeas': ('16359', P(cup=152)),
 'lentils': ('16069', P(cup=192, tbsp=12, tsp=4)),
 'onion': ('11282', {}), 'garlic': ('11215', {}), 'tomato': ('11529', {}),
 'bell pepper': ('11821', {}), 'carrot': ('11124', {}), 'celery': ('11143', {}),
 'potato': ('11352', P(unit=213)), 'broccoli': ('11090', {}), 'spinach': ('11457', {}),
 'mushroom': ('11260', {}), 'zucchini': ('11477', {}), 'corn': ('11167', P(cup=145)),
 'avocado': ('09037', P(unit=136)), 'lettuce': ('11251', P(cup=47)), 'cucumber': ('11205', {}),
 'lemon': ('09150', P(tbsp=0, tsp=0)), 'lime': ('09159', P(tbsp=0, tsp=0)),
 'apple': ('09003', {}), 'banana': ('09040', {}),
 'olive oil': ('04053', P(tbsp=13.5, tsp=4.5)), 'vegetable oil': ('04582', {}),
 'sugar': ('19335', P(tsp=4.2)), 'brown sugar': ('19334', {}), 'honey': ('19296', {}),
 'maple syrup': ('19353', {}), 'soy sauce': ('16123', {}), 'ketchup': ('11935', P(tbsp=17, tsp=5.7)),
 'mayonnaise': ('04025', P(tbsp=13.8, tsp=4.6)), 'mustard': ('02046', {}),
 'peanut butter': ('16098', {}), 'salt': ('02047', {}), 'black pepper': ('02030', {}),
 'chili powder': ('02009', P(tbsp=8, tsp=2.7)), 'cumin': ('02014', {}), 'paprika': ('02028', P(tbsp=6.8, tsp=2.3)),
 'cinnamon': ('02010', P(tbsp=7.9, tsp=2.6)), 'vanilla extract': ('02050', {}),
 'baking powder': ('18369', P(tsp=4.6, tbsp=13.8)), 'baking soda': ('18372', {}),
 'almonds': ('12061', {}), 'walnuts': ('12155', {}), 'chicken broth': ('06194', {}),
 'vegetable broth': ('06700', {}), 'white wine': ('14106', {}), 'pork chop': ('10036', P(unit=150)),
 'turkey breast': ('05710', {}), 'ham': ('07029', {}), 'sausage': ('07036', P(unit=91)),
 'ground pork': ('10219', {}), 'tuna': ('15121', P(unit=120)),
 'basil': ('02044', P(cup=24, tbsp=1.5, tsp=0.5)), 'cilantro': ('11165', P(cup=16, tbsp=1, tsp=0.33)), 'parsley': ('11297', {}), 'ginger': ('11216', {}),
 'jalapeno': ('11979', {}), 'green onion': ('11291', {}), 'rosemary': ('02063', {}), 'thyme': ('02049', {}),
 'oregano': ('02027', {}), 'cauliflower': ('11135', {}), 'kale': ('11233', {}), 'sweet potato': ('11507', {}),
 'asparagus': ('11011', {}), 'green beans': ('11052', {}), 'peas': ('11304', {}), 'cabbage': ('11109', {}),
 'eggplant': ('11209', {}), 'beet': ('11080', {}), 'orange': ('09200', {}), 'strawberry': ('09316', {}),
 'blueberry': ('09050', {}), 'grapes': ('09132', {}), 'pineapple': ('09266', {}), 'mango': ('09176', {}),
 'watermelon': ('09326', {}), 'raisins': ('09298', {}), 'coconut milk': ('12118', P(cup=226)),
 'sesame oil': ('04058', {}), 'rice vinegar': ('02053', {}), 'balsamic vinegar': ('02069', {}),
 'worcestershire sauce': ('06971', {}), 'hot sauce': ('06168', P(tsp=4.7, tbsp=14)),
 'sesame seeds': ('12023', {}), 'chia seeds': ('12006', {}), 'coconut, shredded': ('12108', {}),
 'cashews': ('12087', {}), 'cream of mushroom soup': ('06043', {}),
 'diced tomatoes, canned': ('11531', {}), 'tomato paste': ('11546', {}), 'tomato sauce': ('11549', {}),
 'coconut sugar': None, 'cod': ('15015', {}), 'tilapia': ('15261', {}), 'crab': ('15141', P(cup=135)),
 'scallops': ('15172', P(unit=15)), 'mussels': ('15164', {}), 'lobster': ('15147', {}),
 'almond milk': ('14091', {}), 'oat milk': None, 'soy milk': ('16139', {}), 'cottage cheese': ('01012', {}),
 'feta cheese': ('01019', {}), 'goat cheese': ('01159', {}), 'ricotta cheese': ('01036', {}),
 'blue cheese': ('01004', {}), 'brie cheese': ('01006', {}), 'swiss cheese': ('01040', {}),
 'couscous': ('20028', P(cup=173, tbsp=11, tsp=3.6)), 'barley': ('20005', P(cup=200, tbsp=12, tsp=4)),
 'cornmeal': ('20022', {}), 'buckwheat': ('20009', P(cup=164)),
 'rice noodles': ('20133', P(cup=0)), 'egg noodles': ('20109', P(cup=38)),
 'kidney beans': ('16145', {}), 'pinto beans': ('16345', P(cup=169)), 'edamame': ('11211', {}),
 'split peas': ('16085', P(cup=196)), 'navy beans': ('16038', {}), 'radish': ('11429', P(unit=9)),
 'turnip': ('11564', {}), 'leek': ('11246', {}), 'fennel': ('11957', {}), 'artichoke': ('11007', P(unit=128)),
 'brussels sprouts': ('11098', {}), 'snap peas': ('11300', {}), 'okra': ('11278', {}),
 'butternut squash': ('11485', {}), 'pumpkin': ('11422', {}), 'peach': ('09236', {}), 'pear': ('09252', {}),
 'cherries': ('09070', {}), 'kiwi': ('09148', P(unit=69)), 'cranberries': ('09078', {}),
 'dates': ('09421', P(unit=24)), 'figs': ('09089', {}), 'pecans': ('12142', {}), 'pistachios': ('12151', {}),
 'sunflower seeds': ('12036', {}), 'hazelnuts': ('12120', {}), 'pine nuts': ('12147', {}),
 'flaxseed': ('12220', {}), 'agave nectar': ('19912', {}), 'powdered sugar': ('19336', {}),
 'molasses': ('19304', {}), 'cornstarch': ('20027', {}), 'active dry yeast': ('18375', P(tsp=4, tbsp=12)),
 'cocoa powder': ('19165', P(tbsp=5.4)), 'chocolate chips': ('19080', P(cup=170)),
 'dark chocolate': ('19904', {}), 'bbq sauce': ('06150', P(tbsp=17)), 'sriracha': ('06631', {}),
 'teriyaki sauce': ('06112', {}), 'salsa': ('06164', {}), 'pesto': ('06627', {}),
 'tahini': ('12166', {}), 'dijon mustard': None, 'capers': ('02054', {}), 'pickles': ('11937', P(unit=35)),
 'relish': ('11945', {}), 'nutmeg': ('02025', {}), 'cardamom': ('02006', {}), 'turmeric': ('02043', {}),
 'curry powder': ('02015', {}), 'garam masala': None, 'dill': ('02045', P(cup=9, tbsp=0.6, tsp=0.2)),
 'cayenne pepper': ('02031', {}), 'red pepper flakes': ('02031', {}), 'italian seasoning': None,
 'duck': ('05141', {}), 'lamb': ('17224', {}), 'veal': ('17142', {}), 'chorizo': ('07019', {}),
 'hot dog': ('07950', P(unit=52)), 'deli turkey': ('07944', {}), 'orange juice': ('09206', {}),
 'apple juice': ('09016', {}), 'beer': ('14003', {}), 'red wine': ('14096', {}), 'coffee': ('14209', {}),
 'cola': ('14148', {}), 'nutritional yeast': None, 'miso paste': ('16112', {}), 'kimchi': ('11118', {}),
 'sauerkraut': ('11439', {}), 'hummus': ('16158', {}), 'avocado oil': ('04581', {}),
 'peanut oil': ('04042', {}), 'coconut oil': ('04047', {}), 'french fries': None, 'popcorn': ('19034', {}),
 'anchovies': ('15002', {}), 'sardines': ('15088', {}), 'halibut': ('15036', {}), 'trout': ('15240', {}),
 'catfish': ('15234', {}), 'octopus': ('15166', {}), 'calamari': ('15175', {}), 'crawfish': ('15145', {}),
 'provolone cheese': ('01035', {}), 'gouda cheese': ('01022', {}), 'monterey jack cheese': ('01025', {}),
 'colby cheese': ('01011', {}), 'string cheese': ('01028', {}), 'half and half': ('01049', {}),
 'buttermilk': ('01088', {}), 'condensed milk': ('01095', {}), 'evaporated milk': ('01214', {}),
 'skim milk': ('01085', {}), 'whipped cream': ('01054', {}), 'lard': ('04002', {}),
 'shortening': ('04615', {}), 'ghee': ('01003', {}), 'margarine': ('04610', {}),
 'oyster sauce': ('06176', {}), 'fish sauce': ('06179', {}), 'hoisin sauce': ('06175', {}),
 'chili garlic sauce': None, 'ranch dressing': ('04639', {}), 'italian dressing': ('04114', {}),
 'caesar dressing': ('43015', {}), 'vinaigrette': None, 'applesauce': ('09019', {}),
 'cranberry sauce': ('09081', {}), 'gravy': ('06116', {}), 'alfredo sauce': None,
 'marinara sauce': ('06931', {}), 'allspice': ('02001', {}), 'cloves': ('02011', {}),
 'fennel seed': ('02018', {}), 'mustard seed': ('02024', {}), 'coriander seed': ('02013', {}),
 'star anise': ('02002', {}), 'saffron': ('02037', {}), 'sumac': None, "za'atar": None,
 'smoked paprika': ('02028', {}), 'marshmallow': ('19116', {}), 'graham cracker': ('18173', P(unit=15)),
 'vanilla wafer': ('18213', {}), 'brown rice syrup': None, 'stevia': None, 'coconut water': ('12119', {}),
 'tea': ('14355', {}), 'hot chocolate': ('01105', {}), 'sports drink': ('14461', {}), 'seitan': None,
 'tempeh': ('16114', {}), 'jackfruit': ('09144', {}), 'protein powder': ('14066', P(unit=30)),
 'bison': ('17149', {}), 'venison': ('17164', {}), 'quorn': None, 'bok choy': ('11116', {}),
 'collard greens': ('11161', {}), 'swiss chard': ('11147', {}), 'watercress': ('11591', {}),
 'arugula': ('11959', {}), 'endive': ('11213', {}), 'radicchio': ('11952', {}), 'jicama': ('11603', {}),
 'plantain': ('09277', {}), 'yuca': ('11134', {}), 'water chestnut': ('11590', P(cup=140)),
 'bamboo shoots': ('11028', P(cup=131)), 'bean sprouts': ('11043', {}), 'snow peas': ('11300', P(cup=98)),
 'cantaloupe': ('09181', {}), 'honeydew': ('09184', {}), 'plum': ('09279', {}), 'apricot': ('09021', {}),
 'guava': ('09139', {}), 'papaya': ('09226', {}), 'pomegranate': ('09286', {}), 'blackberries': ('09042', {}),
 'raspberries': ('09302', {}), 'lychee': ('09164', P(unit=10)), 'passion fruit': ('09231', {}),
 'tangerine': ('09218', P(unit=76)), 'grapefruit': ('09112', {}), 'millet': ('20031', P(cup=200)),
 'farro': None, 'wild rice': ('20088', P(cup=160)), 'polenta': ('20022', P(cup=157)),
 'grits': None, 'bulgur': ('20012', P(cup=140)), 'spelt flour': None, 'rye flour': ('20064', P(cup=102)),
 'tapioca': ('20068', {}), 'fava beans': ('16053', {}), 'black eyed peas': ('16063', {}),
 'lima beans': ('16072', {}), 'soybeans': ('16108', P(cup=186)), 'macadamia nuts': ('12131', {}),
 'brazil nuts': ('12078', {}), 'pumpkin seeds': ('12014', P(cup=129)),
}
# new ingredients: key -> (NDB, portions)
ADD = {
 # cooked versions for grains people measure after cooking
 'cooked white rice': ('20045', P(cup=158)), 'cooked rice': ('20045', P(cup=158)),
 'cooked brown rice': ('20037', P(cup=195)), 'cooked pasta': ('20121', P(cup=140)),
 'cooked quinoa': ('20137', P(cup=185)), 'cooked couscous': ('20029', P(cup=157)),
 'cooked lentils': ('16070', P(cup=198)), 'cooked barley': ('20006', P(cup=157)),
 'cooked egg noodles': ('20110', P(cup=160)), 'cooked rice noodles': ('20134', P(cup=176)),
 'cooked bulgur': ('20013', P(cup=182)), 'cooked wild rice': ('20089', P(cup=164)),
 'dried black beans': ('16014', P(cup=194)), 'dried chickpeas': ('16056', P(cup=200)),
 'dried kidney beans': ('16032', P(cup=184)), 'dried pinto beans': ('16042', P(cup=193)),
 # meat & seafood
 'lean ground beef': ('23562', {}), 'extra lean ground beef': ('23472', {}),
 'sirloin steak': ('13929', {}), 'flank steak': ('23657', {}), 'ribeye steak': ('13097', {}),
 'beef tenderloin': ('13917', {}), 'stewing beef': ('23093', {}), 'pork tenderloin': ('10060', {}),
 'pork shoulder': ('10070', {}), 'ground chicken': ('05332', {}), 'chicken wings': ('05100', P(unit=34)),
 'chicken legs': ('05075', {}), 'turkey bacon': ('07254', P(unit=16)), 'salami': ('07926', P(unit=10)),
 'sockeye salmon': ('15085', {}), 'haddock': ('15033', {}), 'mahi mahi': ('15023', {}),
 'swordfish': ('15110', {}), 'clams': ('15157', P(unit=20)), 'oysters': ('15167', P(unit=14)),
 # eggs & dairy
 'egg white': ('01124', P(unit=33, cup=243)), 'egg yolk': ('01125', P(unit=17)),
 '2% milk': ('01079', P(cup=244, tbsp=15, tsp=5)), 'unsalted butter': ('01145', P(cup=227, tbsp=14, tsp=5)),
 'plain yogurt': ('01116', P(cup=245, tbsp=15, tsp=5)), 'kefir': ('01289', P(cup=243, tbsp=15)),
 'vanilla ice cream': ('19095', P(cup=132)), 'american cheese': ('01253', P(unit=21)),
 'mozzarella cheese, fresh': ('01026', {}),
 # produce
 'shallot': ('11677', P(tbsp=10, unit=25)), 'red cabbage': ('11112', P(cup=89)),
 'iceberg lettuce': ('11252', P(cup=72)), 'romaine lettuce': ('11251', P(cup=47)),
 'shiitake mushrooms': ('11238', P(unit=19, cup=72)), 'portobello mushroom': ('11265', P(unit=84, cup=86)),
 'parsnip': ('11298', P(cup=133, unit=170)), 'celery root': ('11141', P(cup=156)),
 'acorn squash': ('11482', P(cup=140)), 'pumpkin puree': ('11424', P(cup=245, tbsp=15)),
 'sun-dried tomatoes': ('11955', P(cup=54, unit=2)), 'roasted red peppers': ('11916', P(cup=140)),
 'green chiles': ('11980', P(cup=139, tbsp=9)), 'black olives': ('09193', P(unit=4.4, tbsp=8.4)),
 'green olives': ('09195', P(unit=2.7)), 'lemon juice': ('09152', P(cup=244, tbsp=15, tsp=5)),
 'lime juice': ('09160', P(cup=242, tbsp=15, tsp=5)), 'red bell pepper': ('11821', P(unit=119)),
 'green bell pepper': ('11333', P(unit=119)), 'corn, canned': ('11176', P(cup=210)),
 # bread, grains, flours
 'whole wheat bread': ('18075', P(unit=32)), 'pita': ('18041', P(unit=60)),
 'corn tortilla': ('18363', P(unit=26)), 'bread flour': ('20083', P(cup=137, tbsp=8.6, tsp=2.9)),
 'almond flour': ('12062', P(cup=96, tbsp=6)), 'chickpea flour': ('16157', P(cup=92, tbsp=6)),
 'buckwheat flour': ('20011', P(cup=120, tbsp=7.5)), 'vital wheat gluten': ('48052', P(cup=120, tbsp=8)),
 'granola': ('08037', P(cup=122)), 'short grain rice': ('20452', P(cup=200)),
 # pantry
 'almond butter': ('12195', P(tbsp=16, cup=250)), 'coconut cream': ('12115', P(tbsp=15, cup=240)),
 'corn syrup': ('19350', P(tbsp=22, cup=341)), 'cream of chicken soup': ('06016', P(cup=252)),
 'apple cider vinegar': ('02048', P(tbsp=14.9, cup=239)), 'white vinegar': ('02053', P(tbsp=14.9, cup=238)),
 'red wine vinegar': ('02068', P(tbsp=14.9, cup=239)),
 # dried herbs & spices
 'garlic powder': ('02020', P(tsp=3.1, tbsp=9.7)), 'onion powder': ('02026', P(tsp=2.4, tbsp=6.9)),
 'ground ginger': ('02021', P(tsp=1.8, tbsp=5.2)), 'dried basil': ('02003', P(tsp=0.7, tbsp=2.1)),
 'dried thyme': ('02042', P(tsp=1, tbsp=2.8)), 'dried rosemary': ('02036', P(tsp=1.2, tbsp=3.3)),
 'dried parsley': ('02029', P(tsp=0.5, tbsp=1.6)), 'sage': ('02038', P(tsp=0.7, tbsp=2)),
 'bay leaf': ('02004', P(unit=0.2, tsp=0.6)), 'white pepper': ('02032', P(tsp=2.4, tbsp=7.1)),
 'dried dill': ('02017', P(tsp=1, tbsp=3.1)), 'celery seed': ('02007', P(tsp=2, tbsp=6.5)),
}

FIELDS = [('kcal', 'Energ_Kcal'), ('p', 'Protein'), ('c', 'Carbohydrt'), ('f', 'Lipid_Tot'),
          ('fib', 'Fiber_TD'), ('sug', 'Sugar_Tot'), ('na', 'Sodium'), ('sf', 'FA_Sat'), ('chol', 'Cholestrl')]
def num(x):
    try: return round(float(x), 2)
    except (TypeError, ValueError): return None

def from_sr(ndb):
    r = rows[ndb]; out = {}
    for k, col in FIELDS:
        v = num(r[col])
        if v is None:
            v = 0.0 if k not in ('sf', 'chol') else None
        out[k] = v
    return out

missing = [k for k in old if k not in MAP and k not in ADD]
if missing: raise SystemExit(f'unmapped keys: {missing}')
bad = [k for k, v in {**MAP, **ADD}.items() if v and v[0] not in rows]
if bad: raise SystemExit(f'unknown NDB: {bad}')

new, audit, sources = {}, [], {}
for key, spec in MAP.items():
    o = dict(old.get(key, {}))
    portions = {k: o.get(k, 0) for k in ('cup', 'tbsp', 'tsp', 'unit')}
    if spec is None:
        e = {k: o.get(k, 0) for k, _ in FIELDS[:7]}
        sf, ch = old_extra.get(key, (round(0.15 * o.get('f', 0), 2), 0))
        e['sf'], e['chol'] = sf, ch
        sources[key] = 'estimate (no USDA SR Legacy entry; typical label values)'
    else:
        ndb, ov = spec
        e = from_sr(ndb)
        if e['sf'] is None: e['sf'] = old_extra.get(key, (round(0.15 * e['f'], 2), 0))[0]
        if e['chol'] is None: e['chol'] = old_extra.get(key, (0, 0))[1]
        portions.update(ov)
        sources[key] = f'USDA SR Legacy {ndb}: {desc[ndb]}'
    e.update(portions)
    new[key] = e
    audit.append((key, sources[key], o.get('kcal'), e['kcal'], o.get('p'), e['p'], o.get('c'), e['c'], o.get('f'), e['f'], o.get('na'), e['na'], o.get('cup'), e['cup'], o.get('unit'), e['unit']))
for key, (ndb, ov) in ADD.items():
    if key in new: raise SystemExit(f'duplicate {key}')
    e = from_sr(ndb)
    if e['sf'] is None: e['sf'] = round(0.15 * e['f'], 2)
    if e['chol'] is None: e['chol'] = 0
    e.update({'cup': 0, 'tbsp': 0, 'tsp': 0, 'unit': 0}); e.update(ov)
    new[key] = e; sources[key] = f'USDA SR Legacy {ndb}: {desc[ndb]}'
    audit.append((key, 'NEW ' + sources[key], None, e['kcal'], None, e['p'], None, e['c'], None, e['f'], None, e['na'], None, e['cup'], None, e['unit']))

def fmt(v):
    v = float(v)
    return str(int(v)) if v == int(v) else (f'{v:.2f}'.rstrip('0').rstrip('.'))
lines = []
for k, e in new.items():
    body = ', '.join(f'{f}:{fmt(e[f])}' for f in ['kcal', 'p', 'c', 'f', 'fib', 'sug', 'na', 'sf', 'chol', 'cup', 'tbsp', 'tsp', 'unit'])
    lines.append(f'  {json.dumps(k)}: {{{body}}}')
open(os.path.join(OUT, 'nutri_db.js'), 'w').write('const NUTRI_DB = {\n' + ',\n'.join(lines) + '\n};')
json.dump(sources, open(os.path.join(OUT, 'sources.json'), 'w'), indent=1)
with open(os.path.join(OUT, 'audit.csv'), 'w', newline='') as fh:
    w = csv.writer(fh); w.writerow(['ingredient', 'source', 'old kcal', 'new kcal', 'old p', 'new p', 'old c', 'new c', 'old f', 'new f', 'old na', 'new na', 'old cup g', 'new cup g', 'old unit g', 'new unit g']); w.writerows(audit)
print(len(new), 'entries;', sum(1 for v in MAP.values() if v is None), 'estimates;', len(ADD), 'added')
