import { useState, useEffect, useRef } from 'react'
import AuthModal from '../components/auth/AuthModal'

// Animated counter hook
function useCounter(target, duration = 2000, start = false) {
  const [count, setCount] = useState(0)
  useEffect(() => {
    if (!start) return
    let startTime = null
    const step = (timestamp) => {
      if (!startTime) startTime = timestamp
      const progress = Math.min((timestamp - startTime) / duration, 1)
      setCount(Math.floor(progress * target))
      if (progress < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }, [start, target, duration])
  return count
}

export default function Landing() {
  const [modalOpen, setModalOpen] = useState(false)
  const [modalView, setModalView] = useState('login')
  const [statsVisible, setStatsVisible] = useState(false)
  const statsRef = useRef(null)

  const predictions = useCounter(12847, 2000, statsVisible)
  const tipsters = useCounter(47, 1500, statsVisible)
  const hitRate = useCounter(68, 1800, statsVisible)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setStatsVisible(true) },
      { threshold: 0.3 }
    )
    if (statsRef.current) observer.observe(statsRef.current)
    return () => observer.disconnect()
  }, [])

  function openModal(view) {
    setModalView(view)
    setModalOpen(true)
  }

  return (
    <div className="min-h-screen bg-[#0F172A] text-white">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-40 bg-[#0F172A]/90 backdrop-blur border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="text-xl font-bold text-white">⚽ LaLigaMarkets</span>
          <div className="flex gap-3">
            <button
              onClick={() => openModal('login')}
              className="px-4 py-2 text-sm text-slate-300 hover:text-white transition-colors"
            >
              Iniciar Sesión
            </button>
            <button
              onClick={() => openModal('signup')}
              className="px-4 py-2 text-sm bg-emerald-500 hover:bg-emerald-400 text-white rounded-xl font-semibold transition-colors"
            >
              Registrarse
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/20 via-[#0F172A] to-amber-900/10 pointer-events-none" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />

        {/* Floating badges */}
        <div className="absolute top-32 left-8 hidden lg:block animate-bounce" style={{ animationDuration: '3s' }}>
          <div className="bg-[#1E293B] border border-emerald-500/30 rounded-2xl px-4 py-3 text-sm">
            <div className="text-emerald-400 font-bold text-lg">12,847</div>
            <div className="text-slate-400">predicciones</div>
          </div>
        </div>
        <div className="absolute top-48 right-12 hidden lg:block animate-bounce" style={{ animationDuration: '4s', animationDelay: '1s' }}>
          <div className="bg-[#1E293B] border border-amber-500/30 rounded-2xl px-4 py-3 text-sm">
            <div className="text-amber-400 font-bold text-lg">68%</div>
            <div className="text-slate-400">hit rate</div>
          </div>
        </div>
        <div className="absolute bottom-32 left-16 hidden lg:block animate-bounce" style={{ animationDuration: '3.5s', animationDelay: '0.5s' }}>
          <div className="bg-[#1E293B] border border-slate-700 rounded-2xl px-4 py-3 text-sm">
            <div className="text-white font-bold text-lg">47</div>
            <div className="text-slate-400">tipsters activos</div>
          </div>
        </div>

        <div className="relative max-w-4xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 rounded-full px-4 py-2 text-emerald-400 text-sm font-medium mb-8">
            <span>🔴</span> En vivo — Mercados Polymarket actualizados
          </div>
          <h1 className="text-4xl md:text-6xl font-black text-white leading-tight mb-6">
            Predicciones de Fútbol Español{' '}
            <span className="text-emerald-400">Powered by</span> los Mejores
            Mercados del Mundo
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10">
            Combinamos las probabilidades en tiempo real de{' '}
            <span className="text-white font-semibold">Polymarket</span> con el
            análisis experto de nuestros tipsters para La Liga y Segunda División.
            Apuesta con ventaja real.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => openModal('signup')}
              className="px-8 py-4 bg-emerald-500 hover:bg-emerald-400 text-white font-bold rounded-2xl text-lg transition-all hover:scale-105"
            >
              Empezar Gratis
            </button>
            <button
              onClick={() => openModal('login')}
              className="px-8 py-4 border border-slate-600 hover:border-emerald-500 text-white font-bold rounded-2xl text-lg transition-all hover:bg-white/5"
            >
              Ver Mercados →
            </button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Todo lo que necesitas para ganar
          </h2>
          <p className="text-slate-400 text-lg">
            Información real, análisis experto, resultados probados.
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: '📊',
              title: 'Datos en Tiempo Real',
              desc: 'Probabilidades respaldadas por dinero real de Polymarket. Sin opiniones sesgadas, solo el mercado.',
            },
            {
              icon: '✅',
              title: 'Tipsters Verificados',
              desc: 'Analistas especializados en La Liga y Segunda División con historial auditado y transparente.',
            },
            {
              icon: '♾️',
              title: 'Sin Límites',
              desc: 'Acceso completo a todos los mercados, análisis y tipsters por solo €5 al mes. Sin letra pequeña.',
            },
          ].map((f) => (
            <div
              key={f.title}
              className="bg-[#1E293B] rounded-2xl p-8 border border-white/5 hover:border-emerald-500/30 transition-colors"
            >
              <div className="text-4xl mb-4">{f.icon}</div>
              <h3 className="text-xl font-bold text-white mb-3">{f.title}</h3>
              <p className="text-slate-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Stats bar */}
      <section ref={statsRef} className="py-16 bg-[#1E293B] border-y border-white/5">
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-3 gap-8 text-center">
          <div>
            <div className="text-4xl font-black text-emerald-400">
              {predictions.toLocaleString()}
            </div>
            <div className="text-slate-400 mt-1">predicciones analizadas</div>
          </div>
          <div>
            <div className="text-4xl font-black text-amber-400">{tipsters}</div>
            <div className="text-slate-400 mt-1">tipsters activos</div>
          </div>
          <div>
            <div className="text-4xl font-black text-white">{hitRate}%</div>
            <div className="text-slate-400 mt-1">hit rate promedio</div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-24 max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Un plan. Sin complicaciones.
          </h2>
          <p className="text-slate-400 text-lg">Acceso total por el precio de una cerveza al mes.</p>
        </div>
        <div className="max-w-md mx-auto">
          <div className="backdrop-blur bg-white/5 border border-white/10 rounded-3xl p-10 text-center hover:border-emerald-500/50 transition-colors">
            <div className="inline-block bg-emerald-500/20 text-emerald-400 text-sm font-semibold px-4 py-1 rounded-full mb-6">
              PRO BETTOR
            </div>
            <div className="flex items-end justify-center gap-2 mb-8">
              <span className="text-6xl font-black text-white">€5</span>
              <span className="text-slate-400 text-xl mb-2">/mes</span>
            </div>
            <ul className="text-left space-y-3 mb-8">
              {[
                'Todos los mercados La Liga y Segunda',
                'Probabilidades Polymarket en tiempo real',
                '47 tipsters verificados',
                'Alertas de value bets',
                'Historial completo de predicciones',
                'Análisis pre-partido detallado',
                'Soporte prioritario',
              ].map((feat) => (
                <li key={feat} className="flex items-center gap-3 text-slate-300">
                  <span className="text-emerald-400 font-bold">✓</span>
                  {feat}
                </li>
              ))}
            </ul>
            <button
              onClick={() => openModal('signup')}
              className="w-full py-4 bg-emerald-500 hover:bg-emerald-400 text-white font-bold rounded-2xl text-lg transition-all hover:scale-105"
            >
              Empezar Ahora
            </button>
            <p className="text-slate-400 text-sm mt-4">
              Cancela cuando quieras. Sin compromiso.
            </p>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-24 bg-[#1E293B]/50">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-white text-center mb-16">
            Lo que dicen nuestros usuarios
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                avatar: 'MR',
                name: 'Miguel R.',
                quote:
                  '"Llevo 6 meses usando LaLigaMarkets y mis resultados han mejorado un 30%. Los datos de Polymarket son un game changer."',
              },
              {
                avatar: 'AS',
                name: 'Ana S.',
                quote:
                  '"Por fin una plataforma seria para el fútbol español. Los tipsters son transparentes y los datos son reales."',
              },
              {
                avatar: 'JM',
                name: 'Jorge M.',
                quote:
                  '"€5 al mes es ridículo para la cantidad de información que te dan. Lo recupero en el primer partido de la semana."',
              },
            ].map((t) => (
              <div
                key={t.name}
                className="bg-[#1E293B] rounded-2xl p-8 border border-white/5"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold">
                    {t.avatar}
                  </div>
                  <div>
                    <div className="text-white font-semibold">{t.name}</div>
                    <div className="text-amber-400 text-sm">★★★★★</div>
                  </div>
                </div>
                <p className="text-slate-400 leading-relaxed italic">{t.quote}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <span className="text-xl font-bold text-white">⚽ LaLigaMarkets</span>
            <div className="flex gap-8 text-slate-400 text-sm">
              <span className="hover:text-white cursor-pointer transition-colors">Términos</span>
              <span className="hover:text-white cursor-pointer transition-colors">Privacidad</span>
              <span className="hover:text-white cursor-pointer transition-colors">Contacto</span>
              <span className="hover:text-white cursor-pointer transition-colors">Blog</span>
            </div>
            <p className="text-slate-500 text-sm">© 2026 LaLigaMarkets. Todos los derechos reservados.</p>
          </div>
        </div>
      </footer>

      <AuthModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        initialView={modalView}
      />
    </div>
  )
}
