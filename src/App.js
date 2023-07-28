import { useEffect, useState } from "react";
import Navbar from "./components/Navbar";
import useMediaQuery from "./hooks/useMediaQuery";
import React from "react";
import DotGroup from "./Utils/DotGroup";
import Landing from "./components/Landing";
import LineGradient from "./Utils/LineGradient";
import Skills from "./components/Skills";
import Contact from "./components/Contact";
import { motion } from "framer-motion";
import Designs from "./components/Designs";
import PuffLoader from "react-spinners/PuffLoader";

function App() {
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    setTimeout(() => {
      setLoading(false)
    }, 1000)
  }, [])

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

      { loading ?

        <div className="flex justify-center items-center h-screen">
          <PuffLoader
          color={'#002820'}
          loading={loading}
          size={70}
          />
        </div>


        :
        <>
          <Navbar
          isTopOfPage={isTopOfPage}
          selectedPage = {selectedPage}
          setSelectedPage = {setSelectedPage}
          />


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


          <div className="w-5/6 mx-auto mt-28">
            <motion.div
              margin="0 0 -200px 0"
              amount="all"
              onViewportEnter={() => setSelectedPage("skills")}
            >
              <Skills />
            </motion.div>
          </div>

          <div className="">
            <LineGradient />
          </div>

          {/* designs */}

          {isAboveSmallScreens ? (
            <div className="w-5/6 mx-auto">
              <motion.div margin="0 0 -200px 0" amount="all" onViewportEnter={() => setSelectedPage("designs")}>
                <Designs />
              </motion.div>
            </div>
            ) : (
            <div className="w-11/12 mx-auto">
              <motion.div margin="0 0 -200px 0" amount="all" onViewportEnter={() => setSelectedPage("designs")}>
                <Designs />
              </motion.div>
            </div>
          )}

          <div className="">
            <LineGradient />
          </div>

          {/* Contacts */}

          <div className="w-5/6 mx-auto">
            <motion.div
              margin="0 0 -200px 0"
              amount="all"
              onViewportEnter={() => setSelectedPage("contact")}
            >
              <Contact />
            </motion.div>
          </div>
        </>

      }
    </div>
  );
}

export default App;
