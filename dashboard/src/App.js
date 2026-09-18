import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import './App.css';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000';

function App() {
  const [datos, setDatos] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [busqueda, setBusqueda] = useState('');
  const [filtroComponente, setFiltroComponente] = useState('');
  const [componentesAbiertos, setComponentesAbiertos] = useState({});
  const [darkMode, setDarkMode] = useState(false);

  // Cargar datos del API
  useEffect(() => {
    const cargarDatos = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE}/api/presupuesto/latest`);
        setDatos(response.data);
        setError(null);
      } catch (err) {
        setError(`No se pudo conectar al servidor: ${err.message}`);
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    cargarDatos();
    // Recargar datos cada 5 minutos
    const intervalo = setInterval(cargarDatos, 5 * 60 * 1000);
    return () => clearInterval(intervalo);
  }, []);

  if (loading) {
    return <div className="loading">⏳ Cargando datos presupuestales...</div>;
  }

  if (error) {
    return <div className="error">⚠️ {error}</div>;
  }

  if (!datos) {
    return <div className="error">No hay datos disponibles</div>;
  }

  // Helpers
  const formatMoney = (val) => {
    if (!val) return '$0';
    return '$' + val.toLocaleString('es-CO', { maximumFractionDigits: 0 });
  };

  const formatPercent = (val) => {
    if (!val) return '0%';
    return val.toFixed(1) + '%';
  };

  const toggleComponente = (comp) => {
    setComponentesAbiertos(prev => ({
      ...prev,
      [comp]: !prev[comp]
    }));
  };


  // Datos para gráficos
  const datosCadena = [
    { etapa: 'Definitivo', valor: datos.totales.definitiva },
    { etapa: 'Reservado', valor: datos.totales.reservado },
    { etapa: 'Comprometido', valor: datos.totales.comprometido },
    { etapa: 'Obligado', valor: datos.totales.obligado },
    { etapa: 'Pagado', valor: datos.totales.pagado },
  ];

  const datosDistribucion = datos.componentes.map(c => ({
    nombre: c.nombre.substring(0, 20),
    valor: c.totales.definitiva,
    full: c.nombre,
  }));

  const datosBrechas = [
    { name: 'Sin Reservar', value: datos.brechas.sin_reservar.pct },
    { name: 'Sin Comprometer', value: datos.brechas.sin_comprometer.pct },
    { name: 'Sin Obligar', value: datos.brechas.sin_obligar.pct },
    { name: 'Pagado', value: datos.porcentajes.pagado },
  ];

  const COLORES = ['#DA121A', '#D8A563', '#144E76', '#228B22'];

  return (
    <div className={`app ${darkMode ? 'dark' : ''}`}>
      {/* HEADER */}
      <header className="header">
        <div className="header-container">
          <div className="header-title">
            <h1>📊 Dashboard Presupuestal</h1>
            <p>Secretaría de Educación - Alcaldía de Rionegro</p>
          </div>
          <div className="header-controls">
            <button
              className="btn-dark-mode"
              onClick={() => setDarkMode(!darkMode)}
              title="Toggle dark mode"
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
            <span className="corte">Corte: {datos.corte}</span>
          </div>
        </div>
      </header>

      {/* TARJETAS KPI */}
      <section className="kpi-section">
        <div className="kpis">
          <KpiCard
            label="Presupuesto Definitivo"
            valor={datos.totales.definitiva}
            pct={100}
            icon="💰"
          />
          <KpiCard
            label="Reservado (CDP)"
            valor={datos.totales.reservado}
            pct={datos.porcentajes.reservado}
            icon="📋"
          />
          <KpiCard
            label="Comprometido (RP)"
            valor={datos.totales.comprometido}
            pct={datos.porcentajes.comprometido}
            icon="✓"
          />
          <KpiCard
            label="Obligado (OPS)"
            valor={datos.totales.obligado}
            pct={datos.porcentajes.obligado}
            icon="📦"
          />
          <KpiCard
            label="Pagado"
            valor={datos.totales.pagado}
            pct={datos.porcentajes.pagado}
            icon="✅"
          />
        </div>
      </section>

      {/* BRECHAS */}
      <section className="brechas-section">
        <h2>Brechas de Ejecución</h2>
        <div className="brechas-grid">
          <BrechaCard
            label="Sin Reservar"
            valor={datos.brechas.sin_reservar.valor}
            pct={datos.brechas.sin_reservar.pct}
            desc="Presupuesto sin CDP"
            color="#DA121A"
          />
          <BrechaCard
            label="Sin Comprometer"
            valor={datos.brechas.sin_comprometer.valor}
            pct={datos.brechas.sin_comprometer.pct}
            desc="Presupuesto sin RP"
            color="#D8A563"
          />
          <BrechaCard
            label="Sin Obligar"
            valor={datos.brechas.sin_obligar.valor}
            pct={datos.brechas.sin_obligar.pct}
            desc="Presupuesto sin OPS"
            color="#144E76"
          />
        </div>
      </section>

      {/* GRÁFICOS */}
      <section className="graficos-section">
        <div className="grafico-container">
          <h3>Ejecución por Etapa</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={datosCadena}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="etapa" />
              <YAxis />
              <Tooltip formatter={(value) => formatMoney(value)} />
              <Bar dataKey="valor" fill="#144E76" animationDuration={1000} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="grafico-container">
          <h3>Distribución por Componente</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={datosDistribucion}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 350 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="nombre" type="category" width={350} />
              <Tooltip formatter={(value) => formatMoney(value)} />
              <Bar dataKey="valor" fill="#228B22" animationDuration={1000} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="grafico-container">
          <h3>Ejecución (Dona)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={datosBrechas}
                cx="50%"
                cy="50%"
                innerRadius={80}
                outerRadius={120}
                paddingAngle={2}
                dataKey="value"
                animationDuration={1000}
              >
                {datosBrechas.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORES[index % COLORES.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${value.toFixed(1)}%`} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* BÚSQUEDA Y FILTRO */}
      <section className="search-section">
        <input
          type="text"
          placeholder="🔍 Buscar rubro por nombre o cons_ppt..."
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          className="search-input"
        />
        <select
          value={filtroComponente}
          onChange={(e) => setFiltroComponente(e.target.value)}
          className="filter-select"
        >
          <option value="">Todos los componentes</option>
          {datos.componentes.map(c => (
            <option key={c.nombre} value={c.nombre}>{c.nombre}</option>
          ))}
        </select>
      </section>

      {/* COMPONENTES EXPANDIBLES */}
      <section className="componentes-section">
        <h2>Seguimiento por Componente</h2>
        {datos.componentes
          .filter(c => !filtroComponente || c.nombre === filtroComponente)
          .map(componente => (
            <ComponenteCard
              key={componente.nombre}
              componente={componente}
              abierto={componentesAbiertos[componente.nombre]}
              onToggle={() => toggleComponente(componente.nombre)}
              busqueda={busqueda}
              formatMoney={formatMoney}
              formatPercent={formatPercent}
            />
          ))}
      </section>

      {/* FOOTER */}
      <footer className="footer">
        <p>Datos actualizados al {datos.fecha_generacion}</p>
        <p>Secretaría de Educación - Alcaldía de Rionegro</p>
      </footer>
    </div>
  );
}

// COMPONENTES AUXILIARES

function KpiCard({ label, valor, pct, icon }) {
  return (
    <div className="kpi-card">
      <div className="kpi-icon">{icon}</div>
      <div className="kpi-label">{label}</div>
      <div className="kpi-valor">
        <AnimatedNumber valor={valor} />
      </div>
      <div className="kpi-pct">{pct.toFixed(1)}%</div>
    </div>
  );
}

function BrechaCard({ label, valor, pct, desc, color }) {
  return (
    <div className="brecha-card">
      <div className="brecha-header" style={{ borderTopColor: color }}>
        <h3>{label}</h3>
        <span className="brecha-pct" style={{ color }}>{pct.toFixed(1)}%</span>
      </div>
      <div className="brecha-valor">${(valor / 1000000).toFixed(2)}M</div>
      <div className="brecha-desc">{desc}</div>
      <div className="brecha-bar">
        <div className="brecha-fill" style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: color }}></div>
      </div>
    </div>
  );
}

function ComponenteCard({ componente, abierto, onToggle, busqueda, formatMoney, formatPercent }) {
  const rubrosFiltrados = busqueda
    ? componente.rubros.filter(r =>
        r.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
        r.cons_ppt.toLowerCase().includes(busqueda.toLowerCase())
      )
    : componente.rubros;

  return (
    <div className="componente-card">
      <div className="componente-header" onClick={onToggle}>
        <span className="componente-toggle">
          {abierto ? '▼' : '▶'} {componente.nombre}
        </span>
        <div className="componente-stats">
          <span>{formatMoney(componente.totales.definitiva)}</span>
          <span className="componente-pct">{componente.pct_pagado.toFixed(1)}%</span>
        </div>
      </div>

      {abierto && (
        <div className="componente-content">
          <table className="rubros-table">
            <thead>
              <tr>
                <th>cons_ppt</th>
                <th>Rubro</th>
                <th>Definitivo</th>
                <th>Comprometido</th>
                <th>Pagado</th>
              </tr>
            </thead>
            <tbody>
              {rubrosFiltrados.map(rubro => (
                <tr key={rubro.cons_ppt}>
                  <td className="cons-ppt">{rubro.cons_ppt}</td>
                  <td>{rubro.nombre}</td>
                  <td>{formatMoney(rubro.definitiva)}</td>
                  <td>{formatMoney(rubro.comprometido)}</td>
                  <td>{formatMoney(rubro.pagado)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function AnimatedNumber({ valor }) {
  const [animado, setAnimado] = useState(0);

  useEffect(() => {
    let start = 0;
    const increment = valor / 30;
    const timer = setInterval(() => {
      start += increment;
      if (start >= valor) {
        setAnimado(valor);
        clearInterval(timer);
      } else {
        setAnimado(start);
      }
    }, 20);
    return () => clearInterval(timer);
  }, [valor]);

  return (
    <>
      $
      {(animado / 1000000000).toFixed(2)} B
    </>
  );
}

export default App;
