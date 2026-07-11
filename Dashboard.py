import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")


def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor <1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'



st.title("DASHBOARD DE VENDAS 🛒")


url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title("Filtros")
regiao = st.sidebar.selectbox("Selecione a Região", regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox("Dados de todo o período", value=True)

if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Selecione o Ano', 2020, 2023)

query_string = {'regiao': regiao.lower(), 'ano': ano}
response = requests.get(url, params=query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect("Selecione o(s) vendedor(es)", 
                                           dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## Tabelas
### Tabelas Receitas
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset= 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending= False)

receita_mensal = dados.set_index('Data da Compra').resample('ME')[['Preço']].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categoria = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending= False)


### Tabelas Quantidade de Vendas
qtd_vendas_estados = pd.DataFrame(dados.groupby('Local da compra').agg(Quantidade=('Preço', 'count')))
qtd_vendas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']].merge(qtd_vendas_estados, left_on = 'Local da compra', right_index = True).sort_values('Quantidade', ascending = False)

qtd_vendas_mensal = pd.DataFrame(dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'ME'))['Preço'].count()).reset_index()
qtd_vendas_mensal['Ano'] = qtd_vendas_mensal['Data da Compra'].dt.year
qtd_vendas_mensal['Mes'] = qtd_vendas_mensal['Data da Compra'].dt.month_name()

qtd_vendas_categorias = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending = False)).reset_index()



### Tabelas vendedores
vendedores = pd.DataFrame(
    dados.groupby('Vendedor')[['Preço']].agg(Soma_Preco=('Preço', 'sum'),Quantidade=('Preço', 'count')).reset_index()
    )


## Graficos 
### Graficos Receita
fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat='lat',
                                  lon='lon',
                                  scope='south america',
                                  size='Preço',
                                  template='seaborn',
                                  hover_name='Local da compra',
                                  hover_data={'lat': False, 'lon': False},
                                  title='Receita por Estado')



fig_receita_mensal = px.line(receita_mensal,
                             x='Mes',
                             y='Preço',
                             markers = True,
                             range_y= (0, receita_mensal['Preço'].max() + 1000),
                             color='Ano',
                             line_dash = 'Ano',
                             title='Receita Mensal')
fig_receita_mensal.update_layout(xaxis_title='Mês', yaxis_title='Receita (R$)', legend_title_text='Ano')



fig_receita_estados = px.bar(receita_estados.head(),
                             x = 'Local da compra',
                             y = 'Preço',
                             text_auto= True,
                             title='Top 5 Estados por Receita')
fig_receita_estados.update_layout(yaxis_title='Receita (R$)')



fig_receita_categoria = px.bar(receita_categoria,
                                text_auto= True,
                                title='Receita por Categoria de Produto')
fig_receita_categoria.update_layout(yaxis_title='Receita (R$)')



### Graficos Quantidade de Vendas
fig_mapa_vendas = px.scatter_geo(qtd_vendas_estados, 
                     lat = 'lat', 
                     lon= 'lon', 
                     scope = 'south america', 
                     #fitbounds = 'locations', 
                     template='seaborn', 
                     size = 'Quantidade', 
                     hover_name ='Local da compra', 
                     hover_data = {'lat':False,'lon':False},
                     title = 'Vendas por estado',
                     )


fig_vendas_mensal = px.line(qtd_vendas_mensal, 
              x = 'Mes',
              y='Preço',
              markers = True, 
              range_y = (0,qtd_vendas_mensal.max()), 
              color = 'Ano', 
              line_dash = 'Ano',
              title = 'Quantidade de vendas mensal')    
fig_vendas_mensal.update_layout(yaxis_title='Quantidade de vendas')

fig_vendas_estados = px.bar(qtd_vendas_estados.head(),
                             x ='Local da compra',
                             y = 'Quantidade',
                             text_auto = True,
                             title = 'Top 5 estados'
)
fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas')


fig_vendas_categorias = px.bar(qtd_vendas_categorias,
                               x = 'Categoria do Produto',
                               y = 'Preço',                                
                               text_auto = True,
                               title = 'Vendas por categoria')
fig_vendas_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de vendas')





## Visualizacao no streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores'])

### Aba Receita
with aba1:
    st.header('Receita', text_alignment = 'center', divider="gray")
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="Receita Total",
            value=formata_numero(dados['Preço'].sum(), prefixo = 'R$')
        )
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)

    with col2:
        st.metric(
            label="Quantidade Total de Vendas",
            value=formata_numero(dados.shape[0])
        )
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categoria, use_container_width=True)


### Aba Quantidade de Vendas
with aba2:
    st.header('Quantidade de Vendas', text_alignment = 'center', divider="gray")

    col1, col2 = st.columns(2)
    with col1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_vendas, use_container_width = True)
        st.plotly_chart(fig_vendas_estados, use_container_width = True)

    with col2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensal, use_container_width = True)
        st.plotly_chart(fig_vendas_categorias, use_container_width = True)


### Aba Vendedores
with aba3:
    st.header('Vendedores', text_alignment = 'center', divider="gray")
    
    qtd_vendedores = st.number_input("Quantidade de Vendedores", min_value=1, max_value=10, value=5)
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="Receita Total",
            value=formata_numero(dados['Preço'].sum(), prefixo = 'R$')
        )
        fig_receita_vendedores = px.bar(vendedores.sort_values('Soma_Preco', ascending = False).head(qtd_vendedores),
                                        x = 'Soma_Preco',
                                        y = vendedores['Vendedor'].sort_values(ascending = False).head(qtd_vendedores),
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (receita)',
                                        labels={'Soma_Preco': 'Receita (R$)',
                                                'y': 'Vendedor'}
                                        )
        st.plotly_chart(fig_receita_vendedores, use_container_width = True)

    with col2:  
        st.metric(
            label="Quantidade Total de Vendas",
            value=formata_numero(dados.shape[0])
        )    
        fig_vendas_vendedores = px.bar(vendedores.sort_values('Quantidade', ascending = False).head(qtd_vendedores),
                                        x = 'Quantidade',
                                        y = vendedores['Vendedor'].sort_values(ascending = False).head(qtd_vendedores),
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (quantidade de vendas)',
                                        labels={'Quantidade': 'Quantidade de Vendas (unidades)',
                                                'y': 'Vendedor'}
                                                )
        st.plotly_chart(fig_vendas_vendedores, use_container_width = True)