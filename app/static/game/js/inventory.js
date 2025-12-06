// Inventory Page Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Elementos do DOM
    const itemFilter = document.getElementById('itemFilter');
    const itemCards = document.querySelectorAll('.inventory-item-card');
    const equipmentSlots = document.querySelectorAll('.inventory-equipment-slot');
    const noItemSelected = document.getElementById('no-item-selected');
    const itemDetailsContent = document.getElementById('item-details-content');
    const inventoryTabs = document.querySelectorAll('.inventory-tab');
    const tabPanes = document.querySelectorAll('.inventory-tab-pane');
    
    // Filtro de itens
    if (itemFilter) {
        itemFilter.addEventListener('input', function() {
            const filterText = this.value.toLowerCase();
            
            // Obter a tab ativa
            const activeTab = document.querySelector('.inventory-tab-pane-active');
            const cardsInTab = activeTab.querySelectorAll('.inventory-item-card');
            
            cardsInTab.forEach(card => {
                const itemName = card.dataset.name.toLowerCase();
                if (itemName.includes(filterText)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Helper function para pegar CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Helper function para parse seguro de JSON
    function safeParse(str, fallback) {
        if (str === undefined || str === null || str === '') {
            return fallback;
        }

        if (typeof str === 'object') {
            return str;
        }

        let parsed;
        try {
            parsed = JSON.parse(str);
            return parsed;
        } catch (e) {
            // Ignora e tenta outras abordagens
        }

        try {
            const fixedStr = str.replace(/\\u0027/g, '"');
            parsed = JSON.parse(fixedStr);
            return parsed;
        } catch (e) {
            // Ignora e tenta outra abordagem
        }

        try {
            const fixedStr = str.replace(/'/g, '"');
            parsed = JSON.parse(fixedStr);
            return parsed;
        } catch (e) {
            // Ignora e tenta outra abordagem
        }

        try {
            const fixedStr = str
            .replace(/\\u0022/g, '"')
            .replace(/\\u005C/g, '\\')
            .replace(/\\u002F/g, '/')
            .replace(/\\u000A/g, '\n')
            .replace(/\\u000D/g, '\r')
            .replace(/\\u0009/g, '\t')
            .replace(/\\u0008/g, '\b')
            .replace(/\\u000C/g, '\f');
            parsed = JSON.parse(fixedStr);
            return parsed;
        } catch (e) {
            console.error('Failed to parse string:', str);
            return fallback;
        }
    }

    function safeIsEmpty(obj) {
        if (obj === null || typeof obj !== 'object') {
            return false;
        }
        return Object.keys(obj).length === 0;
    }
    
    // Função para exibir detalhes do item
    function showItemDetails(element) {
        // Mostrar conteúdo de detalhes e esconder placeholder
        noItemSelected.classList.add('inventory-details-hidden');
        itemDetailsContent.classList.remove('inventory-details-hidden');
        
        // Preencher detalhes do item
        document.getElementById('detail-emoji').textContent = element.dataset.emoji;
        document.getElementById('detail-name').textContent = element.dataset.name;
        document.getElementById('detail-description').textContent = element.dataset.description;
        
        // Atualizar badge de raridade
        const rarityBadge = document.getElementById('detail-rarity');
        const rarityDisplay = element.dataset.rarityDisplay || element.dataset.rarity;
        rarityBadge.textContent = rarityDisplay.charAt(0).toUpperCase() + rarityDisplay.slice(1);
        rarityBadge.className = 'inventory-details-rarity inventory-rarity-' + element.dataset.rarity;
        
        // Limpar estatísticas e ações
        const statsContainer = document.getElementById('detail-stats');
        statsContainer.innerHTML = '';
        const itemActions = document.getElementById('item-actions');
        itemActions.innerHTML = '';

        const emptySlot = element.dataset.description == "Nenhum item equipado";

        switch (element.dataset.type) {
            case 'equipment':
                let equipmentHTML = '';
                
                if (!emptySlot) {
                    equipmentHTML += `
                        <div class="equipment-header">
                            <div class="equipment-level">📊 Nível ${element.dataset.minLevel}+</div>
                        </div>
                        
                        <div class="attribute-line" style="font-size: 1.0rem">${element.dataset.stats}</div>
                    `;
                }

                // Atributos em lista vertical única
                const bonusesEq = safeParse(element.dataset.attributeBonuses, {});
                if (Object.keys(bonusesEq).length > 0) {
                    equipmentHTML += `
                        <div class="attributes-section">
                            ${Object.entries(bonusesEq).map(([attr, value]) => `
                                <div class="attribute-line">
                                    <span class="attribute-name">${attr.replace(/_/g, ' ').toUpperCase()}</span>
                                    <span class="attribute-value ${value > 0 ? 'positive' : 'negative'}">
                                        ${value > 0 ? '+' : ''}${value}
                                    </span>
                                </div>
                            `).join('')}
                        </div>
                    `;
                }

                // Habilidade Passiva compacta
                const passiveSkill = safeParse(element.dataset.passiveSkill, {});
                if (!safeIsEmpty(passiveSkill)) {
                    let effectsHTML = '';
                    
                    const formattedEffects = element.dataset.formattedEffects;
                    if (formattedEffects) {
                        effectsHTML = `
                            <div class="skill-effects">
                                <strong>Efeitos:</strong> ${formattedEffects}
                            </div>
                        `;
                    }

                    equipmentHTML += `
                        <div class="passive-skill-section">
                            <div class="skill-header">
                                <span class="skill-name">${passiveSkill.name}</span>
                                <span class="skill-trigger">${element.dataset.trigger}</span>
                            </div>
                            <div class="skill-description">
                                ${passiveSkill.description || ""}
                            </div>
                            ${effectsHTML}
                        </div>
                    `;
                }

                // Receita de Crafting compacta
                const eqRecipe = safeParse(element.dataset.craftingRecipe, {});
                if (!safeIsEmpty(eqRecipe)) {
                    equipmentHTML += `
                        <div class="recipe-section">
                            <div class="recipe-title">⚒️ Receita</div>
                            <div class="recipe-items">
                                ${Object.entries(eqRecipe).map(([material, qty]) => `
                                    <div class="recipe-item">
                                        <span class="material-emoji">📦</span>
                                        <span class="material-name">${material}</span>
                                        <span class="material-quantity">${qty}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }
                
                statsContainer.innerHTML = equipmentHTML;
                
                const isEquipped = element.dataset.equipped === "true";
                if (!emptySlot) {
                    const csrftoken = getCookie('csrftoken');
                    if (isEquipped) {
                        itemActions.innerHTML = '<button class="inventory-btn inventory-btn-unequip">❌ Remover Item</button>';
                        const itemId = element.dataset.id;
                        
                        const unequipButton = itemActions.querySelector('.inventory-btn-unequip');
                        unequipButton.addEventListener('click', async () => {
                            const response = await fetch('/items/inventory/equip/', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': csrftoken
                                },
                                body: JSON.stringify({
                                    item_id: itemId,
                                    action: "unequip"
                                })
                            });

                            const result = await response.json();
                            if (result.success) {
                                alert("Item removido e devolvido ao inventário!");
                                window.location.reload();
                            } else {
                                alert("Erro ao remover: " + result.error);
                            }
                        });
                    }
                    else {
                        itemActions.innerHTML = '<button class="inventory-btn inventory-btn-equip">🎯 Equipar Item</button>';
                        const itemId = element.dataset.id;
                        
                        const equipButton = itemActions.querySelector('.inventory-btn-equip');
                        equipButton.addEventListener('click', async () => {
                            const response = await fetch('/items/inventory/equip/', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': csrftoken
                                },
                                body: JSON.stringify({
                                    item_id: itemId,
                                    action: "equip"
                                })
                            });

                            const result = await response.json();
                            if (result.success) {
                                alert("Item equipado com sucesso!");
                                window.location.reload();
                            } else {
                                alert("Erro ao equipar: " + result.error);
                            }
                        });
                    }
                }
                break;

            case 'consumable':
                statsContainer.innerHTML += `<div class="attribute-line"><span class="attribute-name">Nível mínimo</span><span class="attribute-value">${element.dataset.minLevel}</span></div>`;
                const affected = safeParse(element.dataset.affectedAttributes, []);
                if (affected.length) {
                    statsContainer.innerHTML += `<div class="attribute-line"><span class="attribute-name">Afeta</span><span class="attribute-value">${affected.join(', ')}</span></div>`;
                }
                const bonusesCon = safeParse(element.dataset.attributeBonuses, {});
                for (const [attr, value] of Object.entries(bonusesCon)) {
                    statsContainer.innerHTML += `<div class="attribute-line"><span class="attribute-name">${attr}</span><span class="attribute-value ${value > 0 ? 'positive' : 'negative'}">${value > 0 ? '+' : ''}${value}</span></div>`;
                }
                itemActions.innerHTML = '<button class="inventory-btn inventory-btn-consume">Consumir</button>';
                break;

            case 'material':
                const recipe = safeParse(element.dataset.craftingRecipe, []);
                if (recipe.length) {
                    statsContainer.innerHTML += `<div class="attribute-line"><span class="attribute-name">Usado para craftar</span></div>`;
                }
                break;
        }
    }
    
    // Adicionar event listeners para os cards
    [...itemCards, ...equipmentSlots].forEach(card => {
        card.addEventListener('click', function() {
            // Remover seleção anterior
            document.querySelectorAll('.inventory-item-card.inventory-item-selected').forEach(el => {
                el.classList.remove('inventory-item-selected');
            });
            
            // Adicionar seleção atual (apenas para cards de inventário)
            if (this.classList.contains('inventory-item-card')) {
                this.classList.add('inventory-item-selected');
            }
            
            showItemDetails(this);
        });
    });
    
    // Controle das tabs
    inventoryTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const target = this.dataset.target;
            
            // Remover classe active de todas as tabs
            inventoryTabs.forEach(t => t.classList.remove('inventory-tab-active'));
            
            // Adicionar classe active à tab clicada
            this.classList.add('inventory-tab-active');
            
            // Esconder todas as tab panes
            tabPanes.forEach(pane => {
                pane.classList.remove('inventory-tab-pane-active');
            });
            
            // Mostrar a tab pane correspondente
            const targetPane = document.getElementById(target);
            if (targetPane) {
                targetPane.classList.add('inventory-tab-pane-active');
            }
            
            // Limpar filtro de busca
            if (itemFilter) {
                itemFilter.value = '';
                const cardsInTab = targetPane.querySelectorAll('.inventory-item-card');
                cardsInTab.forEach(card => {
                    card.style.display = 'flex';
                });
            }
        });
    });

    // Animação de entrada para os itens
    const itemCardsAll = document.querySelectorAll('.inventory-item-card');
    itemCardsAll.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.4s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 50);
    });

    // Efeito de brilho para itens raros
    itemCardsAll.forEach(card => {
        const rarity = card.dataset.rarity;
        if (rarity === 'epic' || rarity === 'legendary') {
            card.classList.add('inventory-item-rare-glow');
        }
    });

    // Tooltips para os slots de equipamento
    equipmentSlots.forEach(slot => {
        slot.addEventListener('mouseenter', function() {
            const emoji = this.querySelector('.slot-icon');
            if (emoji) {
                emoji.style.transform = 'scale(1.2)';
                emoji.style.transition = 'transform 0.3s';
            }
        });
        
        slot.addEventListener('mouseleave', function() {
            const emoji = this.querySelector('.slot-icon');
            if (emoji) {
                emoji.style.transform = 'scale(1)';
            }
        });
    });

    // Efeito de hover para os botões de ação
    document.addEventListener('mouseover', function(e) {
        if (e.target.classList.contains('inventory-btn')) {
            e.target.style.transform = 'translateY(-2px)';
        }
    });

    document.addEventListener('mouseout', function(e) {
        if (e.target.classList.contains('inventory-btn')) {
            e.target.style.transform = 'translateY(0)';
        }
    });

    // Efeito de carregamento inicial
    const page = document.querySelector('.inventory-page');
    page.style.opacity = '0';
    page.style.transition = 'opacity 0.5s ease';
    
    setTimeout(() => {
        page.style.opacity = '1';
    }, 100);
});