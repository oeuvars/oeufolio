import { useEffect, useState } from "react";
import Navbar from "./components/Navbar";
import useMediaQuery from "./hooks/useMediaQuery";
import React from "react";
import DotGroup from "./components/DotGroup";
import Landing from "./components/Landing";
import LineGradient from "./components/LineGradient";
import MySkills from "./components/mySkills";
import Contact from "./components/Contact";
import { motion } from "framer-motion";
import Projects from "./components/Projects";

function App() {
  const [selectedPage, setSelectedPage] = useState("Home");
  const [isTopOfPage, setIsTopOfPage] = useState(true);
  const isAboveMediumScreens = useMediaQuery("(min-width: 1060px)");
  const isAboveSmallScreens = useMediaQuery("(min-width: 768px)");

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY === 0) {
        setIsTopOfPage(true);
        setSelectedPage("home");
      }
      if (window.scrollY !== 0) setIsTopOfPage(false);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);
  return (
    <div className="app scroll-smooth lg:overflow-x-visible md:overflow-x-visible overflow-x-hidden">

      {/* NavBar */}

      <Navbar
        isTopOfPage={isTopOfPage}
        selectedPage = {selectedPage}
        setSelectedPage = {setSelectedPage}
      />

      {/* Landing or Home */}

      <div className="w-5/6 mx-auto md:h-full">
        {isAboveMediumScreens && (
          <DotGroup
            selectedPage={selectedPage}
            setSelectedPage={setSelectedPage}
          />
        )}
        <Landing setSelectedPage={setSelectedPage} />
      </div>

      <LineGradient />

      {/* Skills */}

      <div className="w-5/6 mx-auto md:h-full">
        <motion.div
          margin="0 0 -200px 0"
          amount="all"
          onViewportEnter={() => setSelectedPage("skills")}
        >
          <MySkills />
        </motion.div>
      </div>

      {/* designs */}

      {isAboveSmallScreens ? (
        <div className="w-5/6 mx-auto phone:py-52 tablet:pb-10 sm:pb-10 tablet:pt-0 sm:pt-0 md:pt-0 lg:pt-10">
          <motion.div margin="0 0 -200px 0" amount="all" onViewportEnter={() => setSelectedPage("designs")}>
            <Projects />
          </motion.div>
        </div>
        ) : (
        <div className="w-5/6 mx-auto -my-72">
          <motion.div margin="0 0 -200px 0" amount="all" onViewportEnter={() => setSelectedPage("designs")}>
            <Projects />
          </motion.div>
        </div>
      )}

      {/* Contacts */}

          <div className="w-5/6 mx-auto md:h-full">
            <motion.div
              margin="0 0 -200px 0"
              amount="all"
              onViewportEnter={() => setSelectedPage("contact")}
            >
              <Contact />
            </motion.div>
          </div>
    </div>
  );
}

export default App;
