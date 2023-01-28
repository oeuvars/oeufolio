import React from "react";
import LineGradient from "../components/LineGradient";
import { motion } from "framer-motion";
import day1 from '../assets/1.png';
import day2 from '../assets/14.jpg';
import day3 from '../assets/3.png';
import day4 from '../assets/4.png';
import day5 from '../assets/5.png';
import day6 from '../assets/6.png';
import day7 from "../assets/7.png";
import day8 from "../assets/8.png";
import day9 from "../assets/9.png";
import day10 from "../assets/10.png";
import day11 from "../assets/11.png";
import day12 from "../assets/12.png";
import day13 from "../assets/13.png";
import day14 from "../assets/15.jpg";
import day16 from "../assets/16.jpg";
import day17 from "../assets/17.jpg";

const Projects = () => {
  return (
    <section id="designs" className="tablet:pt-20 pt-48 lg:pt-20 md:pt-20">

      {/* HEADINGS */}
      <motion.div
        className="md:w-2/5 mx-auto text-center"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.5 }}
        transition={{ duration: 0.5 }}
        variants={{
          hidden: { opacity: 0, y: -50 },
          visible: { opacity: 1, y: 0 },
        }}
      >
        <div className="mt-10">
          <p className="font-playfair text-black font-semibold text-4xl">
            DESIGNS
          </p>
          <div className="flex justify-center mt-5">
            <LineGradient width="w-1/3" />
          </div>
        </div>
        <p className="pt-10 text-jet font-medium font-outfit md:pb-10">
          While very diverse, our aesthetic approach often involves distinct sense of play, aiming to put the fun in functional. Strategically, my work aims to elevate design offerings by distilling core messaging down to its clearest and freshest visual form.
        </p>
      </motion.div>

      {/* PROJECTS */}
      <motion.div className="grid md:grid-cols-4 sm:grid-cols-2 gap-12 sm:gap-10 pt-16 pb-12 lg:flex-row lg:flex-wrap">
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day1} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day12} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day3} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day13} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day4} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day11} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day2} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day5} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day6} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day14} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day7} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day8} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day17} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day9} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day10} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
            <motion.div className="scale-100 ease-in hover:scale-105 hover:opacity-90 transition duration-500 basis-1/3 flex-1">
              <img src={day16} alt="" className="rounded-lg mx-auto object-cover drop-shadow-2xl" width={'90%'} height={'90%'} responsive/>
            </motion.div>
          </motion.div>
          <motion.div
        className="md:w-2/5 mx-auto text-center"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.5 }}
        transition={{ duration: 0.5 }}
        variants={{
          hidden: { opacity: 0, y: -50 },
          visible: { opacity: 1, y: 0 },
        }}
      >
        <motion.p className="text-jet font-semibold font-playfair text-lg md:text-2xl mt-5 mb-7 hover:text-jet transition duration-500 ease-in-out">Designing Do Be Hard FR.</motion.p>
      </motion.div>
          <div className="pt-5">
            <LineGradient />
          </div>
    </section>

  );
};

export default Projects;
