// src/components/FlowSystem.jsx

// ── Projeção lat/lon → canvas ─────────────────────────────────
// Mapeia os bounds reais do dataset para uma área retangular no canvas.
// Não usa scale multiplicativo — usa diretamente a área alvo (targetW x targetH)
// com offsetX/offsetY para posicionar na tela.
export function projectLatLon(lat, lon, bounds, targetW, targetH, offsetX, offsetY) {
  const { latMin, latMax, lonMin, lonMax } = bounds
  const x = offsetX + ((lon - lonMin) / (lonMax - lonMin)) * targetW
  const y = offsetY + ((latMax - lat) / (latMax - latMin)) * targetH
  return { x, y }
}

// ── Partícula que corre por uma aresta de hexágono ────────────
class EdgeParticle {
  constructor(p1, p2, flow) {
    this.p1    = p1
    this.p2    = p2
    this.flow  = flow
    this.t     = Math.random()
    this.speed = 0.003 + Math.random() * 0.005
    this.trail = []
    this.maxTrail = 16 + Math.floor(Math.random() * 18)
    this.size  = 0.9 + Math.min(flow, 1) * 1.4
  }

  update() {
    const x = this.p1.x + (this.p2.x - this.p1.x) * this.t
    const y = this.p1.y + (this.p2.y - this.p1.y) * this.t
    this.trail.push({ x, y })
    if (this.trail.length > this.maxTrail) this.trail.shift()
    this.t += this.speed
    if (this.t > 1) this.t = 0
  }

  draw(ctx) {
    if (this.trail.length < 2) return

    for (let i = 0; i < this.trail.length - 1; i++) {
      const ratio = i / this.trail.length
      const alpha = ratio * ratio * 0.65
      const t1 = this.trail[i]
      const t2 = this.trail[i + 1]
      ctx.beginPath()
      ctx.moveTo(t1.x, t1.y)
      ctx.lineTo(t2.x, t2.y)
      ctx.strokeStyle = `rgba(0, 212, 255, ${alpha})`
      ctx.lineWidth   = this.size * ratio * 0.9
      ctx.stroke()
    }

    const head = this.trail[this.trail.length - 1]

    // Glow
    const glow = ctx.createRadialGradient(head.x, head.y, 0, head.x, head.y, this.size * 5)
    glow.addColorStop(0,   'rgba(0, 220, 255, 0.85)')
    glow.addColorStop(0.4, 'rgba(0, 175, 255, 0.25)')
    glow.addColorStop(1,   'rgba(0, 175, 255, 0)')
    ctx.beginPath()
    ctx.arc(head.x, head.y, this.size * 5, 0, Math.PI * 2)
    ctx.fillStyle = glow
    ctx.fill()

    // Núcleo
    ctx.beginPath()
    ctx.arc(head.x, head.y, this.size * 0.65, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(210, 245, 255, 0.95)'
    ctx.fill()
  }
}

// ── Sistema de fluxo ──────────────────────────────────────────
export class FlowSystem {
  constructor(hexagons, bounds, targetW, targetH, offsetX, offsetY) {
    this.particles = []
    const maxFlow  = Math.max(...hexagons.map(h => h.flow || 1))

    hexagons.forEach(hex => {
      const flowNorm = Math.min((hex.flow || 0) / maxFlow, 1)

      // Projeta os vértices reais do hexágono
      const pts = hex.boundary.map(([lat, lon]) =>
        projectLatLon(lat, lon, bounds, targetW, targetH, offsetX, offsetY)
      )

      // Cria partículas em cada uma das 6 arestas
      for (let i = 0; i < pts.length; i++) {
        const p1    = pts[i]
        const p2    = pts[(i + 1) % pts.length]
        const count = flowNorm > 0.6 ? 2 : 1

        for (let c = 0; c < count; c++) {
          this.particles.push(new EdgeParticle(p1, p2, flowNorm))
        }
      }
    })
  }

  update() { this.particles.forEach(p => p.update()) }
  draw(ctx) { this.particles.forEach(p => p.draw(ctx)) }
}