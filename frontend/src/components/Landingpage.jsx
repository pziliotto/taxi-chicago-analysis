// src/components/LandingPage.jsx
import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import data from '../chicago_hexagons.json'
import { FlowSystem, projectLatLon } from './FlowSystem'
 
const BOUNDS = {
  latMin:  41.6596,
  latMax:  42.0222,
  lonMin: -87.8807,
  lonMax: -87.5279,
}
 
// ── Partículas de fundo ───────────────────────────────────────
class BgParticle {
  constructor(canvas) { this.canvas = canvas; this.reset() }
  reset() {
    this.x = Math.random() * this.canvas.width
    this.y = Math.random() * this.canvas.height
    this.vx = (Math.random() - 0.5) * 0.4
    this.vy = (Math.random() - 0.5) * 0.4
    this.life = Math.random() * 0.5 + 0.15
    this.decay = Math.random() * 0.0015 + 0.0004
    this.size = Math.random() * 1.0 + 0.3
    this.trail = []
    this.maxTrail = Math.floor(Math.random() * 12 + 4)
  }
  update() {
    this.trail.push({ x: this.x, y: this.y })
    if (this.trail.length > this.maxTrail) this.trail.shift()
    this.x += this.vx; this.y += this.vy; this.life -= this.decay
    if (this.life <= 0 || this.x < -50 || this.x > this.canvas.width + 50 ||
        this.y < -50 || this.y > this.canvas.height + 50) this.reset()
  }
  draw(ctx) {
    for (let i = 0; i < this.trail.length - 1; i++) {
      const ratio = i / this.trail.length
      ctx.beginPath()
      ctx.moveTo(this.trail[i].x, this.trail[i].y)
      ctx.lineTo(this.trail[i+1].x, this.trail[i+1].y)
      ctx.strokeStyle = `rgba(0,175,255,${ratio * this.life * 0.2})`
      ctx.lineWidth = this.size * ratio
      ctx.stroke()
    }
    ctx.beginPath()
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(0,212,255,${this.life * 0.6})`
    ctx.fill()
  }
}
 
// ── Desenha hexágonos com fade lateral ───────────────────────
function drawHexagons(ctx, canvas, time, hexPts, maxFlow) {
  hexPts.forEach(({ pts, flow }, idx) => {
    const cx       = pts.reduce((s, p) => s + p.x, 0) / pts.length
    const pulse    = Math.sin(time * 0.0012 + idx * 0.25) * 0.5 + 0.5
    const flowNorm = Math.min(flow / maxFlow, 1)
 
    // Fade: invisível até 30% da largura, totalmente visível a partir de 50%
    const fadeStart  = canvas.width * 0.28
    const fadeEnd    = canvas.width * 0.50
    const fadeFactor = Math.max(0, Math.min(1, (cx - fadeStart) / (fadeEnd - fadeStart)))
 
    const alpha = (0.08 + flowNorm * 0.22 + pulse * 0.10) * fadeFactor
 
    ctx.beginPath()
    pts.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y))
    ctx.closePath()
    ctx.strokeStyle = `rgba(0,175,255,${alpha})`
    ctx.lineWidth   = 0.6 + flowNorm * 0.8
    ctx.stroke()
    ctx.fillStyle   = `rgba(0,175,255,${alpha * 0.12})`
    ctx.fill()
  })
}
 
// ── Mini chart ────────────────────────────────────────────────
function MiniChart() {
  const [bars, setBars] = useState(() => Array.from({ length: 14 }, () => Math.random()))
  useEffect(() => {
    const id = setInterval(() => setBars(p => [...p.slice(1), Math.random()]), 1800)
    return () => clearInterval(id)
  }, [])
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 28 }}>
      {bars.map((h, i) => (
        <div key={i} style={{
          width: 7, height: `${h * 100}%`,
          background: `rgba(0,${140 + Math.floor(h * 90)},255,${0.4 + h * 0.5})`,
          transition: 'height 1.6s ease',
        }} />
      ))}
    </div>
  )
}
 
const STATUS_LINES = [
  { text: 'SYSTEM ONLINE',           delay: 0.0 },
  { text: 'CONNECTING...',           delay: 0.5 },
  { text: 'LOADING TRAFFIC DATA...', delay: 1.0 },
  { text: 'INITIALIZING MODULES...', delay: 1.5 },
  { text: 'GIS ENGINE READY',        delay: 2.0 },
  { text: '► READY',                 delay: 2.6 },
]
 
function Corner({ style }) {
  return (
    <div style={{ position: 'absolute', width: 20, height: 20, ...style }}>
      <div style={{
        position: 'absolute', top: 0, left: 0, width: 12, height: 12,
        borderTop: '1px solid rgba(0,175,255,0.5)',
        borderLeft: '1px solid rgba(0,175,255,0.5)',
      }} />
    </div>
  )
}
 
// ── MAIN ──────────────────────────────────────────────────────
export default function LandingPage({ onStart }) {
  const canvasRef = useRef(null)
  const frameRef  = useRef(null)
  const bgParts   = useRef([])
  const flowRef   = useRef(null)
  const hexPtsRef = useRef([])
  const maxFlowRef = useRef(1)
 
  useEffect(() => {
    const canvas = canvasRef.current
    const ctx    = canvas.getContext('2d')
    let time     = 0
 
    const buildScene = () => {
      canvas.width  = window.innerWidth
      canvas.height = window.innerHeight
 
      // A cidade ocupa do centro até a borda direita, com padding vertical
      // targetW e targetH definem o "espaço de desenho" dentro do canvas
      // offsetX empurra o mapa para a direita
      const padding = 20
      const targetW = canvas.width  * 0.72   // largura da área do mapa
      const targetH = canvas.height - padding * 2
      const offsetX = canvas.width  * 0.26   // começa em 26% da tela
      const offsetY = padding
 
      maxFlowRef.current = Math.max(...data.hexagons.map(h => h.flow || 1))
 
      // Pré-computa pontos projetados
      hexPtsRef.current = data.hexagons.map(hex => ({
        flow: hex.flow || 0,
        pts:  hex.boundary.map(([lat, lon]) =>
          projectLatLon(lat, lon, BOUNDS, targetW, targetH, offsetX, offsetY)
        ),
      }))
 
      bgParts.current = Array.from({ length: 100 }, () => new BgParticle(canvas))
 
      // FlowSystem usa os mesmos parâmetros de projeção
      flowRef.current = new FlowSystem(
        data.hexagons, BOUNDS, targetW, targetH, offsetX, offsetY
      )
    }
 
    buildScene()
    window.addEventListener('resize', buildScene)
 
    const loop = () => {
      time++
      ctx.fillStyle = 'rgba(5,5,5,0.20)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
 
      // Grid
      ctx.strokeStyle = 'rgba(0,175,255,0.022)'
      ctx.lineWidth = 0.5
      for (let x = 0; x < canvas.width; x += 60) {
        ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x, canvas.height); ctx.stroke()
      }
      for (let y = 0; y < canvas.height; y += 60) {
        ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(canvas.width,y); ctx.stroke()
      }
 
      bgParts.current.forEach(p => { p.update(); p.draw(ctx) })
      drawHexagons(ctx, canvas, time, hexPtsRef.current, maxFlowRef.current)
      if (flowRef.current) { flowRef.current.update(); flowRef.current.draw(ctx) }
 
      frameRef.current = requestAnimationFrame(loop)
    }
    loop()
 
    return () => {
      window.removeEventListener('resize', buildScene)
      cancelAnimationFrame(frameRef.current)
    }
  }, [])
 
  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', overflow: 'hidden', background: '#050505' }}>
      <canvas ref={canvasRef} style={{ position: 'absolute', inset: 0 }} />
 
      <Corner style={{ top: 12, left: 12 }} />
      <Corner style={{ top: 12, right: 12, transform: 'scaleX(-1)' }} />
      <Corner style={{ bottom: 12, left: 12, transform: 'scaleY(-1)' }} />
      <Corner style={{ bottom: 12, right: 12, transform: 'scale(-1)' }} />
 
      {/* Top bar */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0,
        borderBottom: '1px solid rgba(0,175,255,0.12)',
        background: 'rgba(5,5,5,0.75)', backdropFilter: 'blur(6px)',
        padding: '9px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <span style={{ color: '#00CFFF', fontSize: 9, letterSpacing: 4 }}>
          CTAS // CHICAGO TRAFFIC ANALYSIS SYSTEM
        </span>
        <span style={{ color: 'rgba(245,245,245,0.5)', fontSize: 9, letterSpacing: 3 }}>
          v1.0.0 // 17.7M TRIPS
        </span>
      </div>
 
      {/* Left HUD */}
      <motion.div
        initial={{ opacity: 0, x: -16 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        style={{ position: 'absolute', left: 20, top: 60, display: 'flex', flexDirection: 'column', gap: 8 }}
      >
        <div style={{
          border: '1px solid rgba(0,175,255,0.25)', background: 'rgba(0,12,24,0.85)',
          padding: '12px 16px', backdropFilter: 'blur(8px)', minWidth: 200,
        }}>
          <div style={{ color: '#00CFFF', fontSize: 8, letterSpacing: 3, marginBottom: 8 }}>◈ SYSTEM STATUS</div>
          {STATUS_LINES.map((line, i) => (
            <motion.div key={i}
              initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: line.delay, duration: 0.35 }}
              style={{
                color: line.text.startsWith('►') ? '#00D4FF' : '#FFFFFF',
                fontSize: 10, letterSpacing: 2, marginBottom: 4,
                fontFamily: 'Courier New, monospace',
                opacity: line.text.startsWith('►') ? 1 : 0.85,
              }}
            >
              {line.text}
            </motion.div>
          ))}
        </div>
 
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.8 }}
          style={{ border: '1px solid rgba(0,175,255,0.18)', background: 'rgba(0,12,24,0.8)', padding: '10px 14px', backdropFilter: 'blur(6px)' }}
        >
          <div style={{ color: '#00CFFF', fontSize: 8, letterSpacing: 3, marginBottom: 7 }}>◈ NETWORK ACTIVITY</div>
          <MiniChart />
          <div style={{ marginTop: 7, display: 'flex', gap: 5, alignItems: 'center' }}>
            {[1,2,3,4,5].map(i => (
              <motion.div key={i}
                animate={{ opacity: [0.2, 1, 0.2] }}
                transition={{ duration: 1.8, delay: i * 0.3, repeat: Infinity }}
                style={{ width: 5, height: 5, borderRadius: '50%', background: '#00AFFF' }}
              />
            ))}
            <span style={{ color: '#FFFFFF', fontSize: 8, letterSpacing: 2, opacity: 0.7 }}>LIVE</span>
          </div>
        </motion.div>
 
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 3.0 }}
          style={{ border: '1px solid rgba(0,175,255,0.18)', background: 'rgba(0,12,24,0.8)', padding: '10px 14px', backdropFilter: 'blur(6px)' }}
        >
          <div style={{ color: '#00CFFF', fontSize: 8, letterSpacing: 3, marginBottom: 7 }}>◈ DATASET</div>
          {[['TRIPS','17.7M'],['HEXAGONS','414'],['PERIOD','2022–2026'],['COMMUNITIES','2']].map(([l,v]) => (
            <div key={l} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ color: '#FFFFFF', fontSize: 9, letterSpacing: 2, opacity: 0.75 }}>{l}</span>
              <span style={{ color: '#00D4FF', fontSize: 9, letterSpacing: 2 }}>{v}</span>
            </div>
          ))}
        </motion.div>
      </motion.div>
 
      {/* Hero */}
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        marginLeft: '-16vw', pointerEvents: 'none',
      }}>
        <motion.div
          initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.7 }}
          style={{ color: '#00CFFF', fontSize: 9, letterSpacing: 6, marginBottom: 14 }}
        >
          WELCOME TO
        </motion.div>
 
        <motion.h1
          initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.8 }}
          style={{
            fontSize: 'clamp(22px, 3.2vw, 46px)', fontFamily: 'Courier New, monospace',
            fontWeight: 700, letterSpacing: 5, textAlign: 'center',
            color: '#FFFFFF', textShadow: '0 0 40px rgba(0,175,255,0.5)',
            lineHeight: 1.25, maxWidth: 520,
          }}
        >
          CHICAGO TRAFFIC<br />
          <span style={{ color: '#00AFFF' }}>ANALYSIS SYSTEM</span>
        </motion.h1>
 
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.1 }}
          style={{ color: 'rgba(255,255,255,0.45)', fontSize: 9, letterSpacing: 4, marginTop: 14, marginBottom: 36, textAlign: 'center' }}
        >
          VERSION 1.0.0 // GEOSPATIAL URBAN FLOW ANALYSIS
        </motion.div>
 
        <motion.div
          initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ delay: 1.3, duration: 0.5 }}
          style={{ width: 240, height: 1, background: 'linear-gradient(90deg, transparent, #00AFFF, transparent)', marginBottom: 36 }}
        />
 
        <motion.button
          initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.6 }}
          whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }}
          onClick={onStart}
          style={{
            pointerEvents: 'auto', padding: '13px 44px', background: 'transparent',
            border: '1px solid #00AFFF', color: '#00AFFF',
            fontSize: 13, fontWeight: 700, letterSpacing: 6,
            fontFamily: 'Courier New, monospace', cursor: 'pointer',
            boxShadow: '0 0 20px rgba(0,175,255,0.25), inset 0 0 20px rgba(0,175,255,0.05)',
            transition: 'box-shadow 0.3s, background 0.3s',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.boxShadow = '0 0 48px rgba(0,175,255,0.6), inset 0 0 28px rgba(0,175,255,0.15)'
            e.currentTarget.style.background = 'rgba(0,175,255,0.08)'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.boxShadow = '0 0 20px rgba(0,175,255,0.25), inset 0 0 20px rgba(0,175,255,0.05)'
            e.currentTarget.style.background = 'transparent'
          }}
        >
          START ANALYSIS
        </motion.button>
      </div>
 
      {/* Bottom bar */}
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.2 }}
        style={{
          position: 'absolute', bottom: 0, left: 0, right: 0,
          borderTop: '1px solid rgba(0,175,255,0.08)', background: 'rgba(5,5,5,0.8)',
          backdropFilter: 'blur(6px)', padding: '7px 24px',
          display: 'flex', justifyContent: 'space-between',
        }}
      >
        <span style={{ color: 'rgba(255,255,255,0.35)', fontSize: 8, letterSpacing: 3 }}>
          INFNET // CIÊNCIA DE DADOS // 2026
        </span>
        <span style={{ color: '#00AFFF', fontSize: 8, letterSpacing: 3 }}>
          PÂMELA LIMA ZILIOTTO
        </span>
      </motion.div>
    </div>
  )
}