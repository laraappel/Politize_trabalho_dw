import { Route, Routes } from "react-router-dom";
import Layout from "./components/layout/Layout";
import ColinhaPage from "./pages/ColinhaPage";
import HomePage from "./pages/HomePage";
import NoticiasPage from "./pages/NoticiasPage";
import PoliticoPerfilPage from "./pages/PoliticoPerfilPage";
import PoliticosPage from "./pages/PoliticosPage";
import SobrePage from "./pages/SobrePage";
import TransparenciaPage from "./pages/TransparenciaPage";
import NotFoundPage from "./pages/NotFoundPage";

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/transparencia" element={<TransparenciaPage />} />
        <Route path="/politicos" element={<PoliticosPage />} />
        <Route path="/politicos/:id" element={<PoliticoPerfilPage />} />
        <Route path="/noticias" element={<NoticiasPage />} />
        <Route path="/colinha" element={<ColinhaPage />} />
        <Route path="/sobre" element={<SobrePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default App;
