import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles/global.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)
for (const [k, v] of Object.entries(ElementPlusIconsVue)) {
  app.component(k, v as any)
}
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')
