<script setup lang="ts">
import InquiryDetail from './components/InquiryDetail.vue'
</script>

<template>
  <div class="min-h-screen bg-gray-100">
    <!-- Navbar -->
    <nav class="bg-white shadow-sm">
      <div class="mx-auto max-w-6xl px-4 py-3 flex items-center gap-3">
        <span class="text-lg font-bold text-indigo-700">shiro</span>
        <span class="text-gray-400">/</span>
        <span class="text-sm text-gray-600">Email Agent</span>
      </div>
    </nav>

    <!-- Main content -->
    <main class="mx-auto max-w-6xl">
      <RouterView />
    </main>

    <!-- Detail modal (always mounted, controlled by store) -->
    <InquiryDetail />
  </div>
</template>
