// src/components/Dashboard.jsx
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis,
  Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend
} from 'recharts'
import {
  useSummary, useNeighborhoods, useHourlyFlow,
  useWeeklyFlow, useSeasonalFlow, useRushFlow,
  useTopHexagons, useCommunities
} from '../hooks/useAPI'
 
// ── Paleta ───────────────────────────────────────────────────
const C = {
  bg:       '#050505',
  panel:    'rgba(0,12,24,0.85)',
  border:   'rgba(0,175,255,0.2)',
  accent:   '#00AFFF',
  bright:   '#00D4FF',
  text:     '#FFFFFF',
  muted:    'rgba(255,255,255,0.5)',
  dimmed:   'rgba(255,255,255,0.25)',
}
 
const DAY_LABELS = ['Seg','Ter','Qua','Qui','Sex','Sáb','Dom']
const SEASON_COLORS = {
  Winter: '#4FC3F7', Spring: '#81C784',
  Summer: '#FFB74D', Fall:   '#FF8A65',
}
 
// ── Componentes base ──────────────────────────────────────────
function Panel({ children, style = {} }) {
  return (
    <div style={{
      background:    C.panel,
      border:        `1px solid ${C.border}`,
      backdropFilter:'blur(8px)',
      padding:       '20px',
      borderRadius:  2,
      ...style,
    }}>
      {children}
    </div>
  )
}
 
function PanelTitle({ children }) {
  return (
    <div style={{ color: C.accent, fontSize: 9, letterSpacing: 4, marginBottom: 16, fontFamily: 'Courier New' }}>
      ◈ {children}
    </div>
  )
}
 
function KPI({ label, value, sub }) {
  return (
    <Panel style={{ textAlign: 'center' }}>
      <div style={{ color: C.muted, fontSize: 9, letterSpacing: 3, marginBottom: 8, fontFamily: 'Courier New' }}>
        {label}
      </div>
      <div style={{ color: C.bright, fontSize: 28, fontWeight: 700, fontFamily: 'Courier New', letterSpacing: 2 }}>
        {value}
      </div>
      {sub && <div style={{ color: C.dimmed, fontSize: 9, marginTop: 4, letterSpacing: 2 }}>{sub}</div>}
    </Panel>
  )
}
 
function Loading() {
  return (
    <div style={{ color: C.muted, fontSize: 10, letterSpacing: 3, fontFamily: 'Courier New', padding: 20 }}>
      LOADING...
    </div>
  )
}
 
function NavBtn({ label, active, onClick }) {
  return (
    <button onClick={onClick} style={{
      background:   active ? 'rgba(0,175,255,0.12)' : 'transparent',
      border:       `1px solid ${active ? C.accent : 'rgba(0,175,255,0.2)'}`,
      color:        active ? C.bright : C.muted,
      padding:      '8px 20px',
      fontSize:     10,
      letterSpacing:3,
      fontFamily:   'Courier New',
      cursor:       'pointer',
      transition:   'all 0.2s',
    }}>
      {label}
    </button>
  )
}
 
// ── Tooltip customizado ───────────────────────────────────────
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: 'rgba(0,12,24,0.95)', border: `1px solid ${C.border}`, padding: '8px 12px' }}>
      <div style={{ color: C.accent, fontSize: 9, letterSpacing: 2, marginBottom: 4, fontFamily: 'Courier New' }}>
        {label}
      </div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: C.text, fontSize: 11, fontFamily: 'Courier New' }}>
          {p.name}: <span style={{ color: C.bright }}>{Number(p.value).toLocaleString()}</span>
        </div>
      ))}
    </div>
  )
}
 
// ── Páginas ───────────────────────────────────────────────────
 
// OVERVIEW
function PageOverview() {
  const { data: summary } = useSummary()
  const { data: hourly }  = useHourlyFlow()
  const { data: nbhoods } = useNeighborhoods()
 
  const top5 = nbhoods?.slice(0, 5) || []
 
  return (
    <div style={{ display: 'grid', gap: 16 }}>
      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
        <KPI label="TOTAL DE CORRIDAS"   value={summary ? `${(summary.total_trips / 1e6).toFixed(1)}M` : '—'} sub="2022–2026" />
        <KPI label="TICKET MÉDIO"        value={summary ? `$${summary.avg_ticket}` : '—'} sub="por corrida" />
        <KPI label="DISTÂNCIA MÉDIA"     value={summary ? `${summary.avg_miles} mi` : '—'} sub="por corrida" />
        <KPI label="DURAÇÃO MÉDIA"       value={summary ? `${summary.avg_duration_min} min` : '—'} sub="por corrida" />
      </div>
 
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Fluxo por hora */}
        <Panel>
          <PanelTitle>FLUXO POR HORA DO DIA</PanelTitle>
          {hourly ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={hourly} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                <XAxis dataKey="hour" tick={{ fill: C.muted, fontSize: 9, fontFamily: 'Courier New' }} />
                <YAxis tick={{ fill: C.muted, fontSize: 9, fontFamily: 'Courier New' }} width={50}
                  tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="trips" name="Corridas" radius={[2,2,0,0]}>
                  {hourly.map((_, i) => (
                    <Cell key={i} fill={
                      (i >= 7 && i <= 9) || (i >= 17 && i <= 19)
                        ? C.bright : C.accent
                    } fillOpacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <Loading />}
          <div style={{ color: C.dimmed, fontSize: 8, letterSpacing: 2, marginTop: 8, fontFamily: 'Courier New' }}>
            AZUL CLARO = RUSH HOUR (7–9H E 17–19H)
          </div>
        </Panel>
 
        {/* Top bairros */}
        <Panel>
          <PanelTitle>TOP 5 BAIRROS POR VOLUME</PanelTitle>
          {top5.length > 0 ? (
            <div>
              {top5.map((n, i) => {
                const maxTrips = top5[0].total_trips
                const pct = (n.total_trips / maxTrips) * 100
                return (
                  <div key={n.neighborhood} style={{ marginBottom: 14 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ color: C.text, fontSize: 10, fontFamily: 'Courier New', letterSpacing: 1 }}>
                        {i + 1}. {n.neighborhood}
                      </span>
                      <span style={{ color: C.bright, fontSize: 10, fontFamily: 'Courier New' }}>
                        {(n.total_trips / 1e6).toFixed(2)}M
                      </span>
                    </div>
                    <div style={{ height: 3, background: 'rgba(0,175,255,0.1)', borderRadius: 2 }}>
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.8, delay: i * 0.1 }}
                        style={{ height: '100%', background: `linear-gradient(90deg, ${C.accent}, ${C.bright})`, borderRadius: 2 }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : <Loading />}
        </Panel>
      </div>
 
      {/* Info período */}
      {summary && (
        <Panel style={{ padding: '12px 20px' }}>
          <div style={{ display: 'flex', gap: 40, alignItems: 'center' }}>
            <div>
              <span style={{ color: C.muted, fontSize: 9, letterSpacing: 2, fontFamily: 'Courier New' }}>PERÍODO: </span>
              <span style={{ color: C.bright, fontSize: 9, letterSpacing: 2, fontFamily: 'Courier New' }}>
                {new Date(summary.period_start).toLocaleDateString('pt-BR')} → {new Date(summary.period_end).toLocaleDateString('pt-BR')}
              </span>
            </div>
            <div>
              <span style={{ color: C.muted, fontSize: 9, letterSpacing: 2, fontFamily: 'Courier New' }}>BAIRROS: </span>
              <span style={{ color: C.bright, fontSize: 9, letterSpacing: 2, fontFamily: 'Courier New' }}>{summary.total_neighborhoods}</span>
            </div>
            <div>
              <span style={{ color: C.muted, fontSize: 9, letterSpacing: 2, fontFamily: 'Courier New' }}>HEXÁGONOS H3: </span>
              <span style={{ color: C.bright, fontSize: 9, letterSpacing: 2, fontFamily: 'Courier New' }}>{summary.total_h3_cells}</span>
            </div>
          </div>
        </Panel>
      )}
    </div>
  )
}
 
// TEMPORAL
function PageTemporal() {
  const { data: hourly }   = useHourlyFlow()
  const { data: weekly }   = useWeeklyFlow()
  const { data: seasonal } = useSeasonalFlow()
  const { data: rush }     = useRushFlow()
 
  const weeklyLabeled = weekly?.map(d => ({
    ...d,
    label: DAY_LABELS[d.day_of_week] || d.day_of_week,
  }))
 
  const rushLabeled = rush?.map(d => ({
    ...d,
    label: d.is_rush_hour === 1 ? 'Rush Hour' : 'Fora do Pico',
  }))
 
  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Por hora */}
        <Panel>
          <PanelTitle>CORRIDAS POR HORA</PanelTitle>
          {hourly ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={hourly}>
                <XAxis dataKey="hour" tick={{ fill: C.muted, fontSize: 9, fontFamily: 'Courier New' }} />
                <YAxis tick={{ fill: C.muted, fontSize: 9, fontFamily: 'Courier New' }} width={50}
                  tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="trips" name="Corridas"
                  stroke={C.bright} strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <Loading />}
        </Panel>
 
        {/* Por dia da semana */}
        <Panel>
          <PanelTitle>CORRIDAS POR DIA DA SEMANA</PanelTitle>
          {weeklyLabeled ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={weeklyLabeled}>
                <XAxis dataKey="label" tick={{ fill: C.muted, fontSize: 9, fontFamily: 'Courier New' }} />
                <YAxis tick={{ fill: C.muted, fontSize: 9, fontFamily: 'Courier New' }} width={55}
                  tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="trips" name="Corridas" fill={C.accent} fillOpacity={0.8} radius={[2,2,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <Loading />}
        </Panel>
      </div>
 
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Por estação */}
        <Panel>
          <PanelTitle>CORRIDAS POR ESTAÇÃO DO ANO</PanelTitle>
          {seasonal ? (
            <div>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie data={seasonal} dataKey="trips" nameKey="season"
                    cx="50%" cy="50%" outerRadius={70} strokeWidth={0}>
                    {seasonal.map(d => (
                      <Cell key={d.season} fill={SEASON_COLORS[d.season] || C.accent} fillOpacity={0.85} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    formatter={(v) => <span style={{ color: C.text, fontSize: 9, fontFamily: 'Courier New', letterSpacing: 2 }}>{v}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 8 }}>
                {seasonal.map(d => (
                  <div key={d.season} style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: SEASON_COLORS[d.season], fontSize: 9, fontFamily: 'Courier New', letterSpacing: 1 }}>
                      {d.season}
                    </span>
                    <span style={{ color: C.text, fontSize: 9, fontFamily: 'Courier New' }}>
                      {(d.trips / 1e6).toFixed(2)}M
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : <Loading />}
        </Panel>
 
        {/* Rush vs fora de pico */}
        <Panel>
          <PanelTitle>RUSH HOUR VS FORA DO PICO</PanelTitle>
          {rushLabeled ? (
            <div>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={rushLabeled} layout="vertical">
                  <XAxis type="number" tick={{ fill: C.muted, fontSize: 9, fontFamily: 'Courier New' }}
                    tickFormatter={v => `${(v/1e6).toFixed(1)}M`} />
                  <YAxis type="category" dataKey="label" width={100}
                    tick={{ fill: C.text, fontSize: 9, fontFamily: 'Courier New' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="trips" name="Corridas" fill={C.accent} fillOpacity={0.8} radius={[0,2,2,0]} />
                </BarChart>
              </ResponsiveContainer>
              {rushLabeled.map(d => (
                <div key={d.label} style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
                  <span style={{ color: C.muted, fontSize: 9, fontFamily: 'Courier New', letterSpacing: 2 }}>{d.label} — TICKET MÉDIO</span>
                  <span style={{ color: C.bright, fontSize: 9, fontFamily: 'Courier New' }}>${d.avg_ticket}</span>
                </div>
              ))}
            </div>
          ) : <Loading />}
        </Panel>
      </div>
    </div>
  )
}
 
// BAIRROS
function PageBairros() {
  const { data: nbhoods } = useNeighborhoods()
  const [selected, setSelected] = useState(null)
 
  const sorted = nbhoods?.slice().sort((a, b) => b.total_trips - a.total_trips) || []
 
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
      {/* Lista de bairros */}
      <Panel style={{ maxHeight: 560, overflowY: 'auto' }}>
        <PanelTitle>BAIRROS — CLIQUE PARA DETALHES</PanelTitle>
        {sorted.length > 0 ? sorted.map((n, i) => (
          <div
            key={n.neighborhood}
            onClick={() => setSelected(n.neighborhood)}
            style={{
              padding:      '8px 10px',
              marginBottom: 4,
              cursor:       'pointer',
              background:   selected === n.neighborhood ? 'rgba(0,175,255,0.12)' : 'transparent',
              border:       `1px solid ${selected === n.neighborhood ? C.accent : 'transparent'}`,
              borderRadius: 2,
              transition:   'all 0.15s',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: C.text, fontSize: 10, fontFamily: 'Courier New' }}>
                {i + 1}. {n.neighborhood}
              </span>
              <span style={{ color: C.bright, fontSize: 10, fontFamily: 'Courier New' }}>
                {(n.total_trips / 1000).toFixed(0)}k
              </span>
            </div>
            <div style={{ display: 'flex', gap: 16, marginTop: 2 }}>
              <span style={{ color: C.dimmed, fontSize: 8, fontFamily: 'Courier New', letterSpacing: 1 }}>
                TICKET ${n.avg_ticket}
              </span>
              <span style={{ color: C.dimmed, fontSize: 8, fontFamily: 'Courier New', letterSpacing: 1 }}>
                {n.avg_miles} mi
              </span>
              <span style={{ color: C.dimmed, fontSize: 8, fontFamily: 'Courier New', letterSpacing: 1 }}>
                GORJETA {n.avg_tip_pct}%
              </span>
            </div>
          </div>
        )) : <Loading />}
      </Panel>
 
      {/* Detalhe do bairro selecionado */}
      <div>
        {selected ? (
          <BairroDetail name={selected} />
        ) : (
          <Panel style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ color: C.muted, fontSize: 10, letterSpacing: 3, fontFamily: 'Courier New', textAlign: 'center' }}>
              SELECIONE UM BAIRRO<br />PARA VER DETALHES
            </div>
          </Panel>
        )}
      </div>
    </div>
  )
}
 
function BairroDetail({ name }) {
  const { data, loading } = useNeighborhoodDetail(name)
  if (loading) return <Panel><Loading /></Panel>
  if (!data) return null
 
  const { general, hourly, weekly } = data
  const weeklyLabeled = weekly?.map(d => ({ ...d, label: DAY_LABELS[d.day_of_week] }))
 
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <Panel>
        <PanelTitle>{name.toUpperCase()}</PanelTitle>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {[
            ['CORRIDAS',      (general.total_trips/1000).toFixed(0) + 'k'],
            ['TICKET MÉDIO',  `$${general.avg_ticket}`],
            ['DISTÂNCIA',     `${general.avg_miles} mi`],
            ['DURAÇÃO',       `${general.avg_duration_min} min`],
            ['GORJETA',       `${general.avg_tip_pct}%`],
            ['VELOCIDADE',    `${general.avg_speed_mph} mph`],
          ].map(([l, v]) => (
            <div key={l}>
              <div style={{ color: C.muted, fontSize: 8, letterSpacing: 2, fontFamily: 'Courier New' }}>{l}</div>
              <div style={{ color: C.bright, fontSize: 14, fontWeight: 700, fontFamily: 'Courier New' }}>{v}</div>
            </div>
          ))}
        </div>
      </Panel>
 
      <Panel>
        <PanelTitle>FLUXO POR HORA</PanelTitle>
        <ResponsiveContainer width="100%" height={140}>
          <BarChart data={hourly}>
            <XAxis dataKey="hour" tick={{ fill: C.muted, fontSize: 8, fontFamily: 'Courier New' }} />
            <YAxis tick={{ fill: C.muted, fontSize: 8, fontFamily: 'Courier New' }} width={40}
              tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="trips" name="Corridas" fill={C.accent} fillOpacity={0.8} radius={[2,2,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </Panel>
 
      <Panel>
        <PanelTitle>FLUXO POR DIA</PanelTitle>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={weeklyLabeled}>
            <XAxis dataKey="label" tick={{ fill: C.muted, fontSize: 8, fontFamily: 'Courier New' }} />
            <YAxis tick={{ fill: C.muted, fontSize: 8, fontFamily: 'Courier New' }} width={40}
              tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="trips" name="Corridas" fill={C.accent} fillOpacity={0.8} radius={[2,2,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </Panel>
    </div>
  )
}
 
// Hook inline para detalhe do bairro
function useNeighborhoodDetail(name) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const { default: axios } = require('axios') // lazy import
  
  useState(() => {
    if (!name) return
    setLoading(true)
    fetch(`http://localhost:8000/neighborhoods/${encodeURIComponent(name)}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [name])
 
  return { data, loading }
}
 
// GRAFO
function PageGrafo() {
  const { data: communities } = useCommunities()
  const { data: hexagons }    = useTopHexagons(20, 'total_flow')
  const { data: byPagerank }  = useTopHexagons(20, 'pagerank')
 
  return (
    <div style={{ display: 'grid', gap: 16 }}>
      {/* Comunidades */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <Panel>
          <PanelTitle>COMUNIDADES DETECTADAS (LEIDEN)</PanelTitle>
          {communities ? (
            <div>
              {communities.map((c, i) => (
                <div key={c.community} style={{
                  padding: '12px 14px', marginBottom: 8,
                  border: `1px solid ${i === 0 ? C.bright : C.border}`,
                  background: i === 0 ? 'rgba(0,212,255,0.06)' : 'transparent',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ color: i === 0 ? C.bright : C.text, fontSize: 11, fontFamily: 'Courier New', fontWeight: 700 }}>
                      COMUNIDADE {c.community}
                    </span>
                    <span style={{ color: C.muted, fontSize: 9, fontFamily: 'Courier New' }}>
                      {c.hexagon_count} hexágonos
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 20 }}>
                    <div>
                      <div style={{ color: C.muted, fontSize: 8, letterSpacing: 2, fontFamily: 'Courier New' }}>FLUXO TOTAL</div>
                      <div style={{ color: C.bright, fontSize: 14, fontWeight: 700, fontFamily: 'Courier New' }}>
                        {(c.total_flow / 1e6).toFixed(1)}M
                      </div>
                    </div>
                    <div>
                      <div style={{ color: C.muted, fontSize: 8, letterSpacing: 2, fontFamily: 'Courier New' }}>PAGERANK MÉDIO</div>
                      <div style={{ color: C.accent, fontSize: 14, fontWeight: 700, fontFamily: 'Courier New' }}>
                        {c.avg_pagerank?.toFixed(4)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              <div style={{ color: C.dimmed, fontSize: 8, letterSpacing: 2, fontFamily: 'Courier New', marginTop: 8 }}>
                MODULARIDADE DO GRAFO: 0.4906 — PARTIÇÃO DE BOA QUALIDADE
              </div>
            </div>
          ) : <Loading />}
        </Panel>
 
        {/* Top por PageRank */}
        <Panel>
          <PanelTitle>TOP 10 HEXÁGONOS — PAGERANK</PanelTitle>
          {byPagerank ? (
            <div>
              {byPagerank.slice(0, 10).map((h, i) => (
                <div key={h.h3_cell} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '6px 0', borderBottom: `1px solid rgba(0,175,255,0.08)`,
                }}>
                  <div>
                    <span style={{ color: C.muted, fontSize: 9, fontFamily: 'Courier New', marginRight: 8 }}>
                      #{i + 1}
                    </span>
                    <span style={{ color: C.text, fontSize: 9, fontFamily: 'Courier New' }}>
                      {h.neighborhood || h.h3_cell.slice(0, 12) + '...'}
                    </span>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ color: C.bright, fontSize: 9, fontFamily: 'Courier New' }}>
                      {h.pagerank?.toFixed(4)}
                    </div>
                    <div style={{ color: C.dimmed, fontSize: 8, fontFamily: 'Courier New' }}>
                      C{h.community}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : <Loading />}
        </Panel>
      </div>
 
      {/* Top por fluxo */}
      <Panel>
        <PanelTitle>TOP 15 HEXÁGONOS POR FLUXO TOTAL</PanelTitle>
        {hexagons ? (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={hexagons.slice(0, 15)} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
              <XAxis dataKey="neighborhood"
                tick={{ fill: C.muted, fontSize: 7, fontFamily: 'Courier New' }}
                interval={0} angle={-20} textAnchor="end" height={40} />
              <YAxis tick={{ fill: C.muted, fontSize: 9, fontFamily: 'Courier New' }} width={60}
                tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="total_flow" name="Fluxo Total" fill={C.accent} fillOpacity={0.8} radius={[2,2,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : <Loading />}
      </Panel>
    </div>
  )
}
 
// ── DASHBOARD PRINCIPAL ───────────────────────────────────────
const PAGES = [
  { id: 'overview',  label: 'OVERVIEW'  },
  { id: 'temporal',  label: 'TEMPORAL'  },
  { id: 'bairros',   label: 'BAIRROS'   },
  { id: 'grafo',     label: 'GRAFO'     },
]
 
export default function Dashboard() {
  const [page, setPage] = useState('overview')
 
  return (
    <div style={{ minHeight: '100vh', background: C.bg, color: C.text, fontFamily: 'Courier New' }}>
      {/* Top bar */}
      <div style={{
        position:     'sticky', top: 0, zIndex: 100,
        background:   'rgba(5,5,5,0.95)', backdropFilter: 'blur(8px)',
        borderBottom: `1px solid ${C.border}`,
        padding:      '0 24px',
        display:      'flex', alignItems: 'center', gap: 0,
      }}>
        {/* Logo */}
        <div style={{ padding: '12px 0', marginRight: 32 }}>
          <div style={{ color: C.bright, fontSize: 10, letterSpacing: 4 }}>CTAS</div>
          <div style={{ color: C.dimmed, fontSize: 7, letterSpacing: 3 }}>CHICAGO TRAFFIC</div>
        </div>
 
        {/* Nav */}
        <div style={{ display: 'flex', gap: 4 }}>
          {PAGES.map(p => (
            <NavBtn key={p.id} label={p.label} active={page === p.id} onClick={() => setPage(p.id)} />
          ))}
        </div>
 
        <div style={{ marginLeft: 'auto', color: C.dimmed, fontSize: 8, letterSpacing: 3 }}>
          17.7M TRIPS // 2022–2026
        </div>
      </div>
 
      {/* Conteúdo */}
      <div style={{ padding: '24px' }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={page}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
          >
            {page === 'overview' && <PageOverview />}
            {page === 'temporal' && <PageTemporal />}
            {page === 'bairros'  && <PageBairros />}
            {page === 'grafo'    && <PageGrafo />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}