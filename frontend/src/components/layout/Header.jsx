import { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  IconBalance,
  IconChecklist,
  IconClose,
  IconHome,
  IconInfo,
  IconMenu,
  IconNews,
  IconUsers,
} from "../icons";

const NAV_ITEMS = [
  { to: "/", label: "Início", icon: IconHome },
  { to: "/transparencia", label: "Transparência", icon: IconBalance },
  { to: "/politicos", label: "Políticos", icon: IconUsers },
  { to: "/noticias", label: "Notícias", icon: IconNews },
  { to: "/colinha", label: "Colinha", icon: IconChecklist },
  { to: "/sobre", label: "Sobre", icon: IconInfo },
];

function Header() {
  const [open, setOpen] = useState(false);

  return (
    <header className="site-header">
      <div className="header-inner">
        <NavLink to="/" className="brand" onClick={() => setOpen(false)}>
          <span className="brand-mark" aria-hidden="true">
            VT
          </span>
          <span className="brand-text">
            <strong>Voto Transparente</strong>
            <small>Informação cívica verificável</small>
          </span>
        </NavLink>

        <button
          type="button"
          className="menu-toggle"
          aria-expanded={open}
          aria-controls="menu-principal"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? <IconClose className="icon" /> : <IconMenu className="icon" />}
          <span>{open ? "Fechar menu" : "Abrir menu"}</span>
        </button>

        <nav id="menu-principal" className={open ? "main-nav is-open" : "main-nav"} aria-label="Principal">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) => (isActive ? "nav-link is-active" : "nav-link")}
              onClick={() => setOpen(false)}
            >
              <Icon className="icon" />
              {label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}

export default Header;
