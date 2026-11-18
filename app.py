import pandas as pd
import streamlit as st
from market_api import MarketAPIError, fetch_price, observation_age_hours

st.set_page_config(page_title='WoW Forever Gold Dashboard', layout='wide')
MARKET='forever.normal.horde.us'
STALE_AFTER_HOURS=24
# Blizzard item IDs; add or remove items to customize your watchlist.
ITEMS={
 'Copper Ore':2770,'Tin Ore':2771,'Silver Ore':2775,'Iron Ore':2772,'Gold Ore':2776,
 'Mithril Ore':3858,'Truesilver Ore':7911,'Thorium Ore':10620,
 'Rough Stone':2835,'Coarse Stone':2836,'Heavy Stone':2838,'Solid Stone':7912,'Dense Stone':12365,
 'Copper Bar':2840,'Tin Bar':3576,'Bronze Bar':2841,'Iron Bar':3575,'Silver Bar':2842,'Gold Bar':3577,'Mithril Bar':3860,
 'Peacebloom':2447,'Silverleaf':765,'Earthroot':2449,'Mageroyal':785,'Briarthorn':2450,
 'Bruiseweed':2453,'Wild Steelbloom':3355,'Grave Moss':3369,'Kingsblood':3356,
 'Liferoot':3357,'Fadeleaf':3818,'Goldthorn':3821,'Khadgar’s Whisker':3358,
 'Swiftthistle':2452,'Stranglekelp':3820,'Wintersbite':3819,
}
CATEGORY={name:('Ore' if 'Ore' in name else 'Bar' if 'Bar' in name else 'Stone' if 'Stone' in name else 'Herb') for name in ITEMS}
SKILL={'Copper Ore':1,'Tin Ore':65,'Silver Ore':75,'Iron Ore':125,'Gold Ore':155,'Mithril Ore':175,'Truesilver Ore':230,'Thorium Ore':245,
 'Peacebloom':1,'Silverleaf':1,'Earthroot':15,'Mageroyal':50,'Briarthorn':70,'Bruiseweed':100,'Wild Steelbloom':115,'Grave Moss':120,'Kingsblood':125,'Liferoot':150,'Fadeleaf':160,'Goldthorn':170,'Khadgar’s Whisker':185,'Swiftthistle':70,'Stranglekelp':85,'Wintersbite':195}

def coins(copper):
 if copper is None or pd.isna(copper): return '—'
 copper=int(copper);return f'{copper//10000}g {(copper%10000)//100}s {copper%100}c'

# The observed price endpoint advertises max-age=60s. Never cache longer.
@st.cache_data(ttl=60,show_spinner=False)
def get_price(item_id):
 try:
  payload, provider_ttl, age = fetch_price(item_id, market=MARKET)
  return payload, provider_ttl, age, None
 except MarketAPIError as exc:
  return None, 0, None, str(exc)

st.title('WoW Forever · Horde Gold Dashboard')
st.caption('US Normal (PvE) · Market: forever.normal.horde.us · Third-party market observations, not guaranteed live sales')
with st.sidebar:
 st.header('Your character')
 level=st.number_input('Character level',1,60,33)
 mining=st.number_input('Mining skill',0,300,110)
 herbalism=st.number_input('Herbalism skill',0,300,150)
 gold=st.number_input('Current gold',0.0,1000000.0,45.0)
 st.header('Farm model')
 fee=st.slider('AH sale fee (%)',0,15,5)
 realized=st.slider('Estimated realized sale price (% of minimum buyout)',40,100,90)
 st.caption('Gathered materials have an opportunity cost when evaluating crafting. Prices reflect listings, not confirmed sales.')
 watched=st.multiselect('Watched materials (limit 20 per refresh)',list(ITEMS),default=['Copper Ore','Tin Ore','Iron Ore','Copper Bar','Tin Bar','Iron Bar','Peacebloom','Briarthorn','Bruiseweed','Heavy Stone'],max_selections=20)
 if st.button('Refresh latest available data',use_container_width=True):
  get_price.clear();st.rerun()

st.info('The provider publishes observations on its own schedule. Refresh fetches the latest available data; it cannot force an in-game scan.')
with st.spinner('Loading watched materials…'):
 rows=[];histories={};errors=[]
 for name in watched:
  item_id=ITEMS[name]
  data,provider_ttl,age,error=get_price(item_id)
  if error: errors.append((name,error));continue
  latest=(data or {}).get('latest') or {}
  series=(data or {}).get('series') or []
  price=latest.get('minBuyout')
  rows.append({'Material':name,'Type':CATEGORY[name],'Item ID':item_id,'Skill required':SKILL.get(name),
   'Copper/unit':price,'Gold/20':price*20/10000 if price is not None else None,
   '7d median copper':latest.get('median7d'),'Quantity listed':latest.get('quantity'),
   'Estimated sold/day':((latest.get('sales') or {}).get('estimatedPerDay') if isinstance(latest.get('sales'),dict) else None),
   'Observed at':latest.get('observedAt'), 'Age (hours)':round(age,2) if age is not None else None,
   'Data status':'Stale' if age is None or age>STALE_AFTER_HOURS else 'Recent',
   'Cache max-age (s)':provider_ttl})
  if series:histories[name]=series


df=pd.DataFrame(rows)
if df.empty:st.error('No price data available. Check internet connectivity and the provider status.');st.stop()
valid=df.dropna(subset=['Copper/unit'])
if errors:
 st.warning(f'{len(errors)} item requests failed; remaining results are displayed. No price is assumed for failed requests.')
 with st.expander('View API errors'):
  for item,message in errors:st.write(f'**{item}:** {message}')
if not df.empty and (df['Data status']=='Stale').any():
 st.warning(f"{int((df['Data status']=='Stale').sum())} materials have observations older than {STALE_AFTER_HOURS} hours. Stale prices are excluded from profitability estimates.")
if valid.empty:st.warning('No current listings found for watched materials. Try refreshing later.')
else:
 c1,c2,c3,c4=st.columns(4)
 c1.metric('Materials with listings',len(valid))
 c2.metric('Gold on hand',f'{gold:.1f}g')
 c3.metric('Mining unlock', 'Iron' if mining>=125 else f'{125-mining} skill to Iron')
 c4.metric('Herbalism unlock','Goldthorn' if herbalism>=170 else f'{170-herbalism} skill to Goldthorn')

st.subheader('Material market screener')
only_accessible=st.checkbox('Show only materials I can gather',value=False)
category=st.multiselect('Material categories',['Ore','Herb','Stone','Bar'],default=['Ore','Herb','Stone','Bar'])
filtered=df[df['Type'].isin(category)].copy()
if only_accessible:
 filtered=filtered[filtered.apply(lambda r: (r['Type']=='Ore' and (pd.isna(r['Skill required']) or mining>=r['Skill required'])) or (r['Type']=='Herb' and (pd.isna(r['Skill required']) or herbalism>=r['Skill required'])) or r['Type'] in ('Stone','Bar'),axis=1)]
filtered['Price/unit']=filtered['Copper/unit'].apply(coins)
filtered['7d median']=filtered['7d median copper'].apply(coins)
st.dataframe(filtered[['Material','Type','Skill required','Price/unit','Gold/20','7d median','Quantity listed','Estimated sold/day','Observed at','Age (hours)','Data status']].sort_values('Gold/20',ascending=False,na_position='last'),hide_index=True,use_container_width=True)

st.subheader('Estimated farming profitability')
st.caption('Enter how many units you actually gather per hour. Defaults are zero to avoid inventing drop rates or node density.')
choices=[x for x in watched if CATEGORY[x] in ('Ore','Herb','Stone')]
selected=st.multiselect('Materials collected on your route',choices,default=[x for x in ['Tin Ore','Iron Ore','Heavy Stone','Bruiseweed'] if x in choices])
outputs=[]
for name in selected:
 price_row=df.loc[df['Material']==name]
 price=price_row['Copper/unit'].iloc[0] if not price_row.empty and price_row['Data status'].iloc[0]=='Recent' else None
 a,b,c=st.columns([3,2,2]);a.write(name)
 units=b.number_input('Units/hour',min_value=0,max_value=1000,value=0,key=f'qty_{name}',label_visibility='collapsed')
 c.write(coins(price) if pd.notna(price) else 'No listing')
 if pd.notna(price):outputs.append((name,units,price*units*(1-fee/100)*(realized/100)/10000))
total=sum(x[2] for x in outputs)
st.metric('Estimated realized gold/hour',f'{total:.2f}g')
if outputs:st.bar_chart(pd.DataFrame(outputs,columns=['Material','Units/hour','Gold/hour']).set_index('Material')['Gold/hour'])

st.subheader('Ore vs. bar conversion')
for ore,bar,mult in [('Copper Ore','Copper Bar',1),('Tin Ore','Tin Bar',1),('Iron Ore','Iron Bar',1),('Silver Ore','Silver Bar',1),('Gold Ore','Gold Bar',1),('Mithril Ore','Mithril Bar',1)]:
 p_ore=df.loc[(df.Material==ore)&(df['Data status']=='Recent'),'Copper/unit'];p_bar=df.loc[(df.Material==bar)&(df['Data status']=='Recent'),'Copper/unit']
 if p_ore.empty or p_bar.empty or pd.isna(p_ore.iloc[0]) or pd.isna(p_bar.iloc[0]):continue
 delta=(p_bar.iloc[0]*(1-fee/100)-p_ore.iloc[0]*mult)/100
 st.write(f'**{ore} → {bar}:** {delta:+.2f} silver per bar (before deposits; assumes {mult} ore/bar).')
st.caption('Bronze requires copper and tin bars and is not modeled above. Ore is treated as an opportunity cost; the auction fee applies to bar sale proceeds only.')

st.subheader('Seven-day price history')
if histories:
 pick=st.selectbox('Material',list(histories))
 series=histories[pick]
 points=[]
 for x in series:
  t=x.get('t');v=x.get('min')
  if t and v is not None:points.append({'Time':pd.to_datetime(t,utc=True),'Gold/unit':v/10000})
 if points:st.line_chart(pd.DataFrame(points).set_index('Time'))
 else:st.info('No usable price history for this item.')
else:st.info('Provider has no historical series for the selected materials.')

st.download_button('Export current watched prices (CSV)',data=df.to_csv(index=False).encode('utf-8'),file_name='wow_forever_us_normal_horde_prices.csv',mime='text/csv')
st.caption('Data: AHledger third-party API · https://ahledger.com/developers · Verify provider licensing before publishing or monetizing. Refresh uses a 60-second in-memory cache. No API data is written to SQLite.')

