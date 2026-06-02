import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
 
const STEPS = [
  { text: 'AUTHENTICATING USER...',          duration: 400  },
  { text: 'LOADING GIS MODULES...',          duration: 600  },
  { text: 'CONNECTING TO DATABASE...',       duration: 500  },
  { text: 'LOADING TRAFFIC DATA...',         duration: 800  },
  { text: 'INITIALIZING GRAPH ENGINE...',    duration: 600  },
  { text: 'BUILDING H3 HEXAGONAL INDEX...',  duration: 700  },
  { text: 'INITIALIZING PREDICTION ENGINE...', duration: 500 },
  { text: 'RENDERING GEOSPATIAL LAYERS...',  duration: 400  },
  { text: 'ALL SYSTEMS OPERATIONAL',         duration: 600  },
  { text: '► READY',                         duration: 800  },
]
 
export default function LoadingSequence({ onDone }) {
  const [visibleSteps, setVisibleSteps] = useState([])
  const [done, setDone]                 = useState(false)
 
  useEffect(() => {
    let elapsed = 0
 
    STEPS.forEach((step, i) => {
      setTimeout(() => {
        setVisibleSteps(prev => [...prev, { ...step, id: i }])
        if (i === STEPS.length - 1) {
          setTimeout(() => setDone(true), 600)
          setTimeout(() => onDone(), 1400)
        }
      }, elapsed)
      elapsed += step.duration
    })
  }, [])
 
  const totalDuration = STEPS.reduce((s, st) => s + st.duration, 0)
 
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: done ? 0 : 1 }}
      transition={{ duration: done ? 0.6 : 0.3 }}
      style={{
        position:       'fixed',
        inset:          0,
        background:     '#050505',
        display:        'flex',
        flexDirection:  'column',
        alignItems:     'center',
        justifyContent: 'center',
        fontFamily:     'Courier New, monospace',
        zIndex:         100,
      }}
    >
      {/* Scanline overlay */}
      <div style={{
        position:   'absolute',
        inset:      0,
        background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,175,255,0.015) 2px, rgba(0,175,255,0.015) 4px)',
        pointerEvents: 'none',
      }} />
 
      {/* Terminal box */}
      <div style={{
        border:     '1px solid rgba(0,175,255,0.3)',
        background: 'rgba(0,12,24,0.9)',
        padding:    '40px 56px',
        width:      540,
        maxWidth:   '90vw',
        backdropFilter: 'blur(12px)',
        boxShadow:  '0 0 60px rgba(0,175,255,0.1)',
        position:   'relative',
      }}>
        {/* Corner accents */}
        {[
          { top: -1, left: -1 },
          { top: -1, right: -1 },
          { bottom: -1, left: -1 },
          { bottom: -1, right: -1 },
        ].map((pos, i) => (
          <div key={i} style={{
            position: 'absolute',
            width: 10, height: 10,
            borderTop:  i < 2 ? '2px solid #00AFFF' : undefined,
            borderBottom: i >= 2 ? '2px solid #00AFFF' : undefined,
            borderLeft:  i % 2 === 0 ? '2px solid #00AFFF' : undefined,
            borderRight: i % 2 === 1 ? '2px solid #00AFFF' : undefined,
            ...pos,
          }} />
        ))}
 
        {/* Header */}
        <div style={{ marginBottom: 28, borderBottom: '1px solid rgba(0,175,255,0.15)', paddingBottom: 16 }}>
          <div style={{ color: '#00AFFF', fontSize: 10, letterSpacing: 4, marginBottom: 4 }}>
            CHICAGO TRAFFIC ANALYSIS SYSTEM
          </div>
          <div style={{ color: 'rgba(245,245,245,0.25)', fontSize: 9, letterSpacing: 3 }}>
            INITIALIZING SUBSYSTEMS // v1.0.0
          </div>
        </div>
 
        {/* Steps */}
        <div style={{ minHeight: 220 }}>
          <AnimatePresence>
            {visibleSteps.map((step) => (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.25 }}
                style={{
                  display:       'flex',
                  alignItems:    'center',
                  gap:           10,
                  marginBottom:  8,
                  fontSize:      11,
                  letterSpacing: 2,
                }}
              >
                {/* Status indicator */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  style={{
                    width:        6,
                    height:       6,
                    borderRadius: '50%',
                    background:   step.text.startsWith('►') ? '#00D4FF' : 'rgba(0,175,255,0.6)',
                    flexShrink:   0,
                    boxShadow:    step.text.startsWith('►')
                      ? '0 0 8px rgba(0,212,255,0.8)'
                      : 'none',
                  }}
                />
                <span style={{
                  color: step.text.startsWith('►')
                    ? '#00D4FF'
                    : step.text.includes('OPERATIONAL') || step.text.includes('READY')
                      ? '#00AFFF'
                      : 'rgba(245,245,245,0.55)',
                  fontWeight: step.text.startsWith('►') ? 700 : 400,
                }}>
                  {step.text}
                </span>
 
                {/* Checkmark para steps concluídos */}
                {step.id < visibleSteps.length - 1 && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    style={{ color: 'rgba(0,175,255,0.5)', marginLeft: 'auto', fontSize: 9 }}
                  >
                    OK
                  </motion.span>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
 
          {/* Cursor piscando */}
          {!done && (
            <motion.span
              animate={{ opacity: [1, 0, 1] }}
              transition={{ duration: 0.8, repeat: Infinity }}
              style={{ color: '#00AFFF', fontSize: 14 }}
            >
              _
            </motion.span>
          )}
        </div>
 
        {/* Progress bar */}
        <div style={{ marginTop: 24, borderTop: '1px solid rgba(0,175,255,0.1)', paddingTop: 16 }}>
          <div style={{
            height:     2,
            background: 'rgba(0,175,255,0.1)',
            borderRadius: 2,
            overflow:   'hidden',
          }}>
            <motion.div
              initial={{ width: '0%' }}
              animate={{ width: done ? '100%' : `${(visibleSteps.length / STEPS.length) * 100}%` }}
              transition={{ duration: 0.3 }}
              style={{
                height:     '100%',
                background: 'linear-gradient(90deg, #00AFFF, #00D4FF)',
                boxShadow:  '0 0 8px rgba(0,175,255,0.6)',
              }}
            />
          </div>
          <div style={{
            display:        'flex',
            justifyContent: 'space-between',
            marginTop:      6,
          }}>
            <span style={{ color: 'rgba(245,245,245,0.2)', fontSize: 8, letterSpacing: 2 }}>
              LOADING
            </span>
            <span style={{ color: 'rgba(0,175,255,0.5)', fontSize: 8, letterSpacing: 2 }}>
              {Math.round((visibleSteps.length / STEPS.length) * 100)}%
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  )
}