// src/components/CloudQuickNav.jsx
import React from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Upload, FileText, BarChart3 } from "lucide-react";

export default function CloudQuickNav() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const container = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0, transition: { staggerChildren: 0.06, when: "beforeChildren" } },
  };

  const item = {
    hidden: { opacity: 0, y: 8 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } },
    hover: { scale: 1.02 },
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-12">
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="w-full max-w-md rounded-2xl p-8 bg-[linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0.01))] border border-border backdrop-blur-md shadow-xl"
      >
        {/* Header */}
        <motion.div variants={item} className="mb-4 text-center">
          <h1 className="text-2xl font-semibold">
            {user?.name ? `Hi ${user.name.split(' ')[0]} 👋` : "Cloud Mode"}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Choose where you want to go — quick actions for cloud workflows.
          </p>
        </motion.div>

        {/* Buttons */}
        <motion.div variants={item} className="mt-6 flex flex-col gap-3">
          <motion.div whileHover="hover" variants={item}>
            <Button
              size="lg"
              className="w-full rounded-full flex items-center justify-center gap-2"
              onClick={() => navigate("/upload")}
            >
              <Upload className="h-4 w-4" />
              Upload File
            </Button>
          </motion.div>

          <motion.div whileHover="hover" variants={item}>
            <Button
              size="lg"
              variant="outline"
              className="w-full rounded-full flex items-center justify-center gap-2"
              onClick={() => navigate("/files")}
            >
              <FileText className="h-4 w-4" />
              My Files
            </Button>
          </motion.div>

          <motion.div whileHover="hover" variants={item}>
            <Button
              size="lg"
              variant="outline"
              className="w-full rounded-full flex items-center justify-center gap-2"
              onClick={() => navigate("/dashboard")}
            >
              <BarChart3 className="h-4 w-4" />
              Analytics
            </Button>
          </motion.div>
        </motion.div>

        {/* Footer note */}
        <motion.div variants={item} className="mt-6 text-center text-xs text-muted-foreground">
          <p>
            Tip: Uploads generate expiring links. Manage them on <span className="font-medium">My Files</span>.
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}
